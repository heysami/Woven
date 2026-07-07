import Foundation

/// Environment probing: Command Line Tools presence, python3 resolution, and
/// login-shell PATH capture. A Finder-launched app inherits a minimal PATH
/// (/usr/bin:/bin:/usr/sbin:/sbin); the daemon resolves the agent CLIs
/// (claude/codex/opencode) via shutil.which only, so the daemon must be
/// spawned with the user's real login-shell PATH or agent detection breaks.
enum EnvProbe {

    private static var cachedPATH: String?

    // MARK: - Command Line Tools

    /// True when xcode-select reports a developer directory. Checked BEFORE
    /// ever invoking /usr/bin/python3: on a Mac without CLT, running the
    /// python3 shim pops Apple's installer dialog at an uncontrolled moment,
    /// so the app shows its own guidance dialog instead.
    static func cltInstalled() -> Bool {
        let r = run("/usr/bin/xcode-select", ["-p"], timeout: 5)
        return r?.status == 0
    }

    /// Fires Apple's Command Line Tools installer UI.
    static func offerCLTInstall() {
        _ = run("/usr/bin/xcode-select", ["--install"], timeout: 5)
    }

    // MARK: - Python

    /// Resolve a python3 that satisfies the daemon's 3.9 floor, searching the
    /// login-shell PATH. Mirrors editor/serve.command's find_python(): same
    /// candidate order, same version gate.
    static func resolvePython() -> String? {
        let candidates = ["python3", "python3.13", "python3.12", "python3.11", "python3.10", "python3.9"]
        let dirs = loginShellPATH().split(separator: ":").map(String.init)
        let fm = FileManager.default
        for cand in candidates {
            for dir in dirs {
                let path = (dir as NSString).appendingPathComponent(cand)
                guard fm.isExecutableFile(atPath: path) else { continue }
                let gate = run(path, ["-c", "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 9) else 1)"], timeout: 10)
                if gate?.status == 0 { return path }
                break // this candidate name resolved but is too old; try next name
            }
        }
        return nil
    }

    // MARK: - Login-shell PATH

    /// The user's real PATH, captured once per app lifetime.
    /// Order of attempts:
    ///   1. `$SHELL -l -i -c 'echo $PATH'` (interactive login: sources .zshrc,
    ///      where nvm/asdf/homebrew shims usually live) with a hard timeout,
    ///      because interactive rc files can hang.
    ///   2. `$SHELL -l -c` (non-interactive login: .zprofile/.zshenv).
    ///   3. Constructed fallback: inherited PATH + the well-known dirs.
    static func loginShellPATH() -> String {
        if let cached = cachedPATH { return cached }
        let shell = ProcessInfo.processInfo.environment["SHELL"] ?? "/bin/zsh"
        var captured: String?
        for flags in [["-l", "-i", "-c"], ["-l", "-c"]] {
            if let r = run(shell, flags + ["echo -n \"$PATH\""], timeout: 3),
               r.status == 0 {
                let path = r.stdout.trimmingCharacters(in: .whitespacesAndNewlines)
                if !path.isEmpty, path.contains("/usr/bin") {
                    captured = path
                    break
                }
            }
        }
        var parts: [String] = (captured ?? ProcessInfo.processInfo.environment["PATH"] ?? "/usr/bin:/bin:/usr/sbin:/sbin")
            .split(separator: ":").map(String.init)
        // Belt-and-suspenders: well-known tool dirs, appended so a captured
        // login PATH keeps its own ordering.
        let home = NSHomeDirectory()
        var extras = ["/opt/homebrew/bin", "/usr/local/bin", home + "/.local/bin", home + "/bin"]
        // Newest installed nvm node bin, if any.
        let nvmVersions = home + "/.nvm/versions/node"
        if let vs = try? FileManager.default.contentsOfDirectory(atPath: nvmVersions), !vs.isEmpty {
            if let newest = vs.sorted(by: { $0.compare($1, options: .numeric) == .orderedDescending }).first {
                extras.append(nvmVersions + "/" + newest + "/bin")
            }
        }
        for e in extras where !parts.contains(e) {
            if FileManager.default.fileExists(atPath: e) { parts.append(e) }
        }
        // Dedupe, preserving order.
        var seen = Set<String>()
        let final = parts.filter { seen.insert($0).inserted }.joined(separator: ":")
        cachedPATH = final
        return final
    }

    // MARK: - Subprocess helper

    /// Run a process with a timeout; returns nil on launch failure or timeout.
    /// Output is accumulated via readabilityHandler to avoid pipe deadlock.
    private static func run(_ exec: String, _ args: [String], timeout: TimeInterval) -> (status: Int32, stdout: String)? {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: exec)
        proc.arguments = args
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = Pipe() // discard, but keep it from mixing into stdout
        var data = Data()
        let lock = NSLock()
        pipe.fileHandleForReading.readabilityHandler = { h in
            let chunk = h.availableData
            if !chunk.isEmpty {
                lock.lock(); data.append(chunk); lock.unlock()
            }
        }
        do { try proc.run() } catch { return nil }
        let sem = DispatchSemaphore(value: 0)
        DispatchQueue.global(qos: .userInitiated).async {
            proc.waitUntilExit()
            sem.signal()
        }
        if sem.wait(timeout: .now() + timeout) == .timedOut {
            proc.terminate()
            _ = sem.wait(timeout: .now() + 1)
            if proc.isRunning { kill(proc.processIdentifier, SIGKILL) }
            pipe.fileHandleForReading.readabilityHandler = nil
            return nil
        }
        pipe.fileHandleForReading.readabilityHandler = nil
        // Drain any remainder left in the pipe after exit.
        if let rest = try? pipe.fileHandleForReading.readToEnd() {
            lock.lock(); data.append(rest); lock.unlock()
        }
        let out = String(data: data, encoding: .utf8) ?? ""
        return (proc.terminationStatus, out)
    }
}
