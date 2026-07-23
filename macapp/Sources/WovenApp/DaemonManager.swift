import Foundation

/// Owns the serve.py lifecycle: probe-then-attach-or-spawn, readiness poll,
/// stdout/stderr capture to ~/Library/Logs/Woven/daemon.log, crash restart
/// with backoff, and SIGTERM-and-wait teardown on quit.
///
/// The probe-first ordering is load-bearing: serve.py lsof-kills any stale
/// serve.py holding its port at boot, so blindly spawning a second daemon
/// would SIGTERM a daemon the user started in Terminal. A healthy responder
/// is attached to, never signalled.
final class DaemonManager {

    enum State: Equatable {
        case idle
        case probing
        case starting
        case running   // managed: we spawned it
        case attached  // pre-existing daemon, not ours to signal
        case failed(String)
    }

    // The probe hits /__healthz, a daemon-only endpoint: a live serve.py
    // answers 200; a static file server rooted at a Woven checkout would
    // serve /editor/ convincingly but 404s /__healthz, so it is correctly
    // classified as foreign.

    private(set) var state: State = .idle {
        didSet {
            NSLog("[woven] daemon state: \(state)")
            DispatchQueue.main.async { self.onStateChange?() }
        }
    }
    var onStateChange: (() -> Void)?
    /// Fired (once per successful start) when GET /editor/ returns 200.
    var onReady: (() -> Void)?

    var ownsDaemon: Bool { process != nil }
    var isServing: Bool { state == .running || state == .attached }

    private let pythonPath: String
    private var process: Process?
    private var logHandle: FileHandle?
    private var userInitiatedStop = false
    private var quitting = false
    private var crashTimes: [Date] = []
    private var readinessDeadline: Date?

    let port = WovenPaths.editorPort

    init(pythonPath: String) {
        self.pythonPath = pythonPath
    }

    // MARK: - Start (probe -> attach or spawn)

    func start() {
        switch state {
        case .idle, .failed: break
        default: return
        }
        state = .probing
        probe { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .woven:
                self.state = .attached
                self.onReady?()
            case .foreign:
                self.state = .failed("Port \(self.port) is in use by another app. Quit it, or set a different port with: defaults write com.heysami.Woven EditorPort <port>")
            case .free:
                self.spawn()
            }
        }
    }

    private enum ProbeResult { case woven, foreign, free }

    private func probe(completion: @escaping (ProbeResult) -> Void) {
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 1.5
        cfg.timeoutIntervalForResource = 1.5
        let session = URLSession(configuration: cfg)
        let url = URL(string: "http://127.0.0.1:\(port)/__healthz")!
        session.dataTask(with: url) { _, resp, _ in
            let result: ProbeResult
            if let http = resp as? HTTPURLResponse {
                result = http.statusCode == 200 ? .woven : .foreign
            } else if resp != nil {
                result = .foreign
            } else {
                result = .free // refused / timed out
            }
            DispatchQueue.main.async { completion(result) }
        }.resume()
    }

    // MARK: - Spawn

    private func spawn() {
        rotateLogIfNeeded()
        let fm = FileManager.default
        try? fm.createDirectory(atPath: WovenPaths.logsDir, withIntermediateDirectories: true)
        if !fm.fileExists(atPath: WovenPaths.daemonLog) {
            fm.createFile(atPath: WovenPaths.daemonLog, contents: nil)
        }
        logHandle = FileHandle(forWritingAtPath: WovenPaths.daemonLog)
        logHandle?.seekToEndOfFile()
        logLine("[app] spawning daemon: \(pythonPath) serve.py (port \(port))")

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: pythonPath)
        proc.arguments = [WovenPaths.currentServePy]
        // Mirror serve.command: cwd = the editor/ dir of the current tree.
        // Using the `current` symlink path means a restart after an update
        // swap picks up the new tree.
        proc.currentDirectoryURL = URL(fileURLWithPath: WovenPaths.currentEditorDir)
        var env = ProcessInfo.processInfo.environment
        env["EDITOR_PORT"] = String(port)
        env["TH_WORKSPACE_DIR"] = WovenPaths.workspaceDir
        env["PATH"] = EnvProbe.loginShellPATH()
        // Marker the daemon surfaces via /__healthz {launcher: "macapp"} so
        // the editor shows app-appropriate restart instructions (menu bar
        // icon, not a terminal command) when the daemon goes down.
        env["WOVEN_MACAPP"] = "1"
        proc.environment = env

        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { [weak self] h in
            let chunk = h.availableData
            guard !chunk.isEmpty else { return }
            self?.logHandle?.write(chunk)
        }
        proc.terminationHandler = { [weak self] p in
            DispatchQueue.main.async { self?.handleTermination(status: p.terminationStatus) }
        }

        do {
            try proc.run()
        } catch {
            state = .failed("Could not start the daemon: \(error.localizedDescription)")
            return
        }
        process = proc
        userInitiatedStop = false
        state = .starting
        // Generous deadline: the very first boot of a fresh 275MB tree can be
        // slowed by pyc compilation + Spotlight indexing the new files.
        readinessDeadline = Date().addingTimeInterval(60)
        pollReadiness()
    }

    private func pollReadiness() {
        guard state == .starting else { return }
        if let deadline = readinessDeadline, Date() > deadline {
            state = .failed("Daemon did not become ready in 60s.\n\(logTail())")
            return
        }
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 1
        let session = URLSession(configuration: cfg)
        let url = URL(string: "http://127.0.0.1:\(port)/editor/")!
        session.dataTask(with: url) { _, resp, err in
            DispatchQueue.main.async { [weak self] in
                guard let self = self, self.state == .starting else { return }
                if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                    NSLog("[woven] readiness poll: 200, firing onReady")
                    self.state = .running
                    self.crashTimes = []
                    self.onReady?()
                } else {
                    if let err = err {
                        NSLog("[woven] readiness poll error: \(err.localizedDescription)")
                    } else {
                        NSLog("[woven] readiness poll: HTTP \((resp as? HTTPURLResponse)?.statusCode ?? -1)")
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { self.pollReadiness() }
                }
            }
        }.resume()
    }

    // MARK: - Termination / crash restart

    private func handleTermination(status: Int32) {
        let died = process
        process = nil
        if quitting || userInitiatedStop {
            state = .idle
            return
        }
        if state == .starting {
            // Died during the readiness window: surface serve.py's own error.
            state = .failed("Daemon exited (status \(status)) while starting.\n\(logTail())")
            return
        }
        // Crash while running: restart with backoff, give up after 3 crashes
        // inside 60s.
        _ = died
        logLine("[app] daemon exited unexpectedly (status \(status))")
        crashTimes.append(Date())
        crashTimes = crashTimes.filter { Date().timeIntervalSince($0) < 60 }
        if crashTimes.count > 3 {
            state = .failed("Daemon keeps crashing - see the log (View Daemon Log).")
            return
        }
        let backoff = pow(2.0, Double(crashTimes.count - 1)) // 1s, 2s, 4s
        logLine("[app] restarting daemon in \(Int(backoff))s")
        state = .starting
        DispatchQueue.main.asyncAfter(deadline: .now() + backoff) { [weak self] in
            guard let self = self, self.state == .starting, self.process == nil else { return }
            self.spawn()
        }
    }

    // MARK: - Stop / restart

    /// SIGTERM the managed daemon and wait for its cleanup handlers (they
    /// SIGTERM agent-CLI children and stop cloudflared tunnels). SIGKILL
    /// after 5s. No-op for attached daemons: never signal what we did not spawn.
    func stopForQuit(completion: @escaping () -> Void) {
        quitting = true
        guard let proc = process, proc.isRunning else {
            completion()
            return
        }
        proc.terminate() // SIGTERM
        DispatchQueue.global(qos: .userInitiated).async {
            let sem = DispatchSemaphore(value: 0)
            DispatchQueue.global().async {
                proc.waitUntilExit()
                sem.signal()
            }
            if sem.wait(timeout: .now() + 5) == .timedOut, proc.isRunning {
                kill(proc.processIdentifier, SIGKILL)
                _ = sem.wait(timeout: .now() + 1)
            }
            DispatchQueue.main.async { completion() }
        }
    }

    /// Restart: SIGTERM the managed daemon (or take over from an attached
    /// one; the caller confirms that first), then probe + spawn fresh.
    func restart() {
        if let proc = process, proc.isRunning {
            userInitiatedStop = true
            proc.terminate()
            DispatchQueue.global().async { [weak self] in
                proc.waitUntilExit()
                DispatchQueue.main.async {
                    self?.process = nil
                    self?.state = .idle
                    self?.start()
                }
            }
        } else {
            // Attached or stopped: spawning is the takeover. serve.py's own
            // stale-holder logic evicts an old serve.py on the port.
            process = nil
            spawnDirectlyAfterTakeover()
        }
    }

    private func spawnDirectlyAfterTakeover() {
        state = .probing
        // Give an evicted daemon a beat, then spawn regardless of probe:
        // takeover is explicit and user-confirmed.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            self?.spawn()
        }
    }

    // MARK: - Local services (first-boot self-heal)

    /// Ensure the tree-local services are installed, via the daemon's own
    /// installer endpoints (the exact calls the onboarding "Install" buttons
    /// make). The product installs these into editor/tools/ from the
    /// onboarding wizard - but the wizard only mounts on an empty landing, so
    /// an app-managed install could sit with "+ New project" disabled on
    /// "Install shader-verify first" and no visible way to fix it. The app
    /// owns its daemon's tree, so it owns keeping the tree serviceable:
    /// probe each package, install what is missing, log the outcome.
    /// Skipped for attached daemons (their tree is user-managed).
    func ensureLocalServices() {
        guard ownsDaemon else { return }
        let packages = ["rembg", "cloudflared", "glslang", "shader-verify"]
        let base = "http://127.0.0.1:\(port)"
        DispatchQueue.global(qos: .utility).async { [weak self] in
            for pkg in packages {
                guard let self = self else { return }
                guard let status = self.syncJSON(url: base + "/__local_status?package=\(pkg)", timeout: 20),
                      (status["installed"] as? Bool) == false else { continue }
                self.logLine("[app] local service \(pkg) missing - installing via /__local_install")
                var req = URLRequest(url: URL(string: base + "/__local_install")!, timeoutInterval: 900)
                req.httpMethod = "POST"
                req.setValue("application/json", forHTTPHeaderField: "Content-Type")
                req.httpBody = try? JSONSerialization.data(withJSONObject: ["package": pkg])
                let sem = DispatchSemaphore(value: 0)
                var ok = false
                URLSession.shared.dataTask(with: req) { data, _, _ in
                    if let data = data,
                       let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] {
                        ok = (obj["ok"] as? Bool) ?? false
                    }
                    sem.signal()
                }.resume()
                _ = sem.wait(timeout: .now() + 900)
                self.logLine("[app] local service \(pkg) install \(ok ? "succeeded" : "failed - see onboarding card")")
            }
        }
    }

    private func syncJSON(url: String, timeout: TimeInterval) -> [String: Any]? {
        guard let u = URL(string: url) else { return nil }
        var out: [String: Any]?
        let sem = DispatchSemaphore(value: 0)
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = timeout
        URLSession(configuration: cfg).dataTask(with: u) { data, _, _ in
            if let data = data {
                out = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            }
            sem.signal()
        }.resume()
        _ = sem.wait(timeout: .now() + timeout + 5)
        return out
    }

    // MARK: - Shares (for the status menu)

    struct ShareLink {
        let label: String
        let url: String
    }

    /// GET /__shares with a tight timeout; called from menuWillOpen.
    func fetchShares(completion: @escaping ([ShareLink]) -> Void) {
        guard isServing else { return completion([]) }
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 0.5
        cfg.timeoutIntervalForResource = 0.5
        let session = URLSession(configuration: cfg)
        let url = URL(string: "http://127.0.0.1:\(port)/__shares")!
        session.dataTask(with: url) { data, _, _ in
            var links: [ShareLink] = []
            if let data = data,
               let obj = try? JSONSerialization.jsonObject(with: data) {
                // Accept both a bare array and {shares: [...]}.
                let items: [[String: Any]]
                if let arr = obj as? [[String: Any]] {
                    items = arr
                } else if let dict = obj as? [String: Any],
                          let arr = dict["shares"] as? [[String: Any]] {
                    items = arr
                } else {
                    items = []
                }
                for item in items {
                    let label = (item["label"] as? String)
                        ?? (item["prototype"] as? String)
                        ?? (item["id"] as? String) ?? "share"
                    for key in ["quickUrl", "wovenUrl", "shareUrl", "lastUrl"] {
                        if let u = item[key] as? String, !u.isEmpty {
                            links.append(ShareLink(label: label, url: u))
                            break
                        }
                    }
                }
            }
            DispatchQueue.main.async { completion(links) }
        }.resume()
    }

    // MARK: - Log helpers

    private func rotateLogIfNeeded() {
        let fm = FileManager.default
        if let attrs = try? fm.attributesOfItem(atPath: WovenPaths.daemonLog),
           let size = attrs[.size] as? Int, size > 5 * 1_048_576 {
            let old = WovenPaths.daemonLog + ".old"
            try? fm.removeItem(atPath: old)
            try? fm.moveItem(atPath: WovenPaths.daemonLog, toPath: old)
        }
    }

    private func logLine(_ s: String) {
        if let data = (s + "\n").data(using: .utf8) {
            logHandle?.write(data)
        }
    }

    private func logTail(bytes: Int = 2000) -> String {
        guard let h = FileHandle(forReadingAtPath: WovenPaths.daemonLog) else { return "" }
        defer { try? h.close() }
        let size = h.seekToEndOfFile()
        let offset = size > UInt64(bytes) ? size - UInt64(bytes) : 0
        h.seek(toFileOffset: offset)
        let data = h.readDataToEndOfFile()
        return String(data: data, encoding: .utf8) ?? ""
    }
}
