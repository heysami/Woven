import Foundation

/// Canonical on-disk locations the app owns.
enum WovenPaths {
    /// User-visible install root: the unpacked release trees live here as
    /// plain, browsable files (same content as the Release zip).
    static let installRoot = NSHomeDirectory() + "/Woven/app"
    static let currentLink = installRoot + "/current"
    static var currentServePy: String { currentLink + "/editor/serve.py" }
    static var currentEditorDir: String { currentLink + "/editor" }

    static let supportDir = NSHomeDirectory() + "/Library/Application Support/Woven"
    static let stateFile = supportDir + "/state.json"

    static let logsDir = NSHomeDirectory() + "/Library/Logs/Woven"
    static let daemonLog = logsDir + "/daemon.log"

    /// TH_WORKSPACE_DIR: projects + workspace.json live here, never touched
    /// by app updates. Overridable via `defaults write com.heysami.Woven WorkspaceDir <path>`.
    static var workspaceDir: String {
        UserDefaults.standard.string(forKey: "WorkspaceDir") ?? NSHomeDirectory() + "/Documents/Woven"
    }

    /// Daemon port. Overridable via `defaults write com.heysami.Woven EditorPort <n>`.
    static var editorPort: Int {
        let v = UserDefaults.standard.integer(forKey: "EditorPort")
        return v > 0 ? v : 5731
    }

    static var editorURL: URL { URL(string: "http://localhost:\(editorPort)/editor/")! }
}

/// Downloads + installs Woven release trees from GitHub Releases.
/// Version discipline: check `tag_name` of releases/latest against the
/// installed marker; download ONLY when they differ. Unpack with ditto
/// (preserves exec bits), commit with an atomic symlink rename.
final class InstallManager: NSObject, URLSessionDownloadDelegate {

    struct State: Codable {
        var installedTag: String?
        var lastCheckAt: Date?
        var pendingTag: String?
    }

    struct Release {
        let tag: String
        let zipURL: URL
    }

    enum InstallError: LocalizedError {
        case badResponse(String)
        case unpackFailed(String)
        case swapFailed(String)
        var errorDescription: String? {
            switch self {
            case .badResponse(let m): return "GitHub release check failed: \(m)"
            case .unpackFailed(let m): return "Could not unpack the Woven release: \(m)"
            case .swapFailed(let m): return "Could not activate the Woven release: \(m)"
            }
        }
    }

    private(set) var state: State
    /// Set while an update sits swapped-in but the daemon still serves the
    /// old tree (restart applies it). Drives the menu hint.
    var updateReadyTag: String? {
        get { state.pendingTag }
        set { state.pendingTag = newValue; saveState() }
    }

    private var isInstalling = false
    private var progressHandler: ((Double, String) -> Void)?
    private var downloadCompletion: ((Result<URL, Error>) -> Void)?
    private var downloadingTag = ""
    private lazy var session: URLSession = URLSession(configuration: .default, delegate: self, delegateQueue: nil)

    static let repoLatestURL = URL(string: "https://api.github.com/repos/heysami/Woven/releases/latest")!

    override init() {
        let fm = FileManager.default
        try? fm.createDirectory(atPath: WovenPaths.supportDir, withIntermediateDirectories: true)
        if let data = fm.contents(atPath: WovenPaths.stateFile),
           let s = try? JSONDecoder.wovenDates().decode(State.self, from: data) {
            state = s
        } else {
            state = State()
        }
        super.init()
    }

    var isInstalled: Bool {
        FileManager.default.fileExists(atPath: WovenPaths.currentServePy)
    }

    private func saveState() {
        if let data = try? JSONEncoder.wovenDates().encode(state) {
            try? data.write(to: URL(fileURLWithPath: WovenPaths.stateFile), options: .atomic)
        }
    }

    // MARK: - Release check

    func fetchLatestRelease(completion: @escaping (Result<Release, Error>) -> Void) {
        var req = URLRequest(url: Self.repoLatestURL, timeoutInterval: 20)
        req.setValue("Woven-mac-app", forHTTPHeaderField: "User-Agent")
        req.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        URLSession.shared.dataTask(with: req) { data, resp, err in
            let finish: (Result<Release, Error>) -> Void = { r in DispatchQueue.main.async { completion(r) } }
            if let err = err { return finish(.failure(err)) }
            guard let http = resp as? HTTPURLResponse, http.statusCode == 200, let data = data else {
                let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
                return finish(.failure(InstallError.badResponse("HTTP \(code)")))
            }
            guard let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
                  let tag = obj["tag_name"] as? String else {
                return finish(.failure(InstallError.badResponse("unexpected JSON")))
            }
            // Prefer a curated .zip release asset; fall back to the source zipball.
            var zip: URL?
            if let assets = obj["assets"] as? [[String: Any]] {
                for a in assets {
                    if let name = a["name"] as? String, name.hasSuffix(".zip"),
                       !name.contains("macos"), // never install the app zip as the Woven tree
                       let u = a["browser_download_url"] as? String {
                        zip = URL(string: u)
                        break
                    }
                }
            }
            if zip == nil, let zb = obj["zipball_url"] as? String { zip = URL(string: zb) }
            guard let zipURL = zip else { return finish(.failure(InstallError.badResponse("no zip in release"))) }
            self.state.lastCheckAt = Date()
            self.saveState()
            finish(.success(Release(tag: tag, zipURL: zipURL)))
        }.resume()
    }

    /// Background check on launch, throttled to once per 6 hours. When a new
    /// tag exists it is downloaded + swapped silently; `onUpdateReady` fires
    /// so the menu can show "Update ready - Restart Daemon to apply".
    func backgroundCheck(onUpdateReady: @escaping (String) -> Void) {
        if let last = state.lastCheckAt, Date().timeIntervalSince(last) < 6 * 3600 { return }
        fetchLatestRelease { [weak self] result in
            guard let self = self, case .success(let rel) = result else { return }
            guard rel.tag != self.state.installedTag else { return }
            self.install(release: rel, progress: { _, _ in }) { r in
                if case .success = r {
                    self.updateReadyTag = rel.tag
                    onUpdateReady(rel.tag)
                }
            }
        }
    }

    // MARK: - Install

    func install(release: Release,
                 progress: @escaping (Double, String) -> Void,
                 completion: @escaping (Result<Void, Error>) -> Void) {
        guard !isInstalling else { return }
        isInstalling = true
        progressHandler = progress
        downloadingTag = release.tag
        let finish: (Result<Void, Error>) -> Void = { [weak self] r in
            DispatchQueue.main.async {
                self?.isInstalling = false
                self?.progressHandler = nil
                completion(r)
            }
        }
        downloadCompletion = { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .failure(let err):
                finish(.failure(err))
            case .success(let tmpZip):
                do {
                    DispatchQueue.main.async { progress(1.0, "Unpacking Woven \(release.tag)...") }
                    try self.unpackAndSwap(zip: tmpZip, tag: release.tag)
                    self.state.installedTag = release.tag
                    self.saveState()
                    self.prune()
                    finish(.success(()))
                } catch {
                    finish(.failure(error))
                }
            }
        }
        var req = URLRequest(url: release.zipURL, timeoutInterval: 600)
        req.setValue("Woven-mac-app", forHTTPHeaderField: "User-Agent")
        session.downloadTask(with: req).resume()
    }

    // MARK: URLSessionDownloadDelegate

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData bytesWritten: Int64, totalBytesWritten: Int64,
                    totalBytesExpectedToWrite: Int64) {
        let frac = totalBytesExpectedToWrite > 0
            ? Double(totalBytesWritten) / Double(totalBytesExpectedToWrite)
            : -1
        let mb = Double(totalBytesWritten) / 1_048_576
        let text = String(format: "Downloading Woven %@... %.0f MB", downloadingTag, mb)
        DispatchQueue.main.async { self.progressHandler?(frac, text) }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didFinishDownloadingTo location: URL) {
        // Move out of the OS temp slot synchronously (the file dies when this
        // delegate returns).
        let dest = FileManager.default.temporaryDirectory
            .appendingPathComponent("woven-release-\(downloadingTag).zip")
        try? FileManager.default.removeItem(at: dest)
        do {
            try FileManager.default.moveItem(at: location, to: dest)
            downloadCompletion?(.success(dest))
        } catch {
            downloadCompletion?(.failure(error))
        }
        downloadCompletion = nil
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            downloadCompletion?(.failure(error))
            downloadCompletion = nil
        }
    }

    // MARK: - Unpack + atomic swap

    private func unpackAndSwap(zip: URL, tag: String) throws {
        let fm = FileManager.default
        try fm.createDirectory(atPath: WovenPaths.installRoot, withIntermediateDirectories: true)
        // Unpack on the destination volume so the final move is a rename.
        let unpackDir = WovenPaths.installRoot + "/.unpack-" + tag
        try? fm.removeItem(atPath: unpackDir)
        let ditto = Process()
        ditto.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
        ditto.arguments = ["-x", "-k", zip.path, unpackDir]
        let errPipe = Pipe()
        ditto.standardError = errPipe
        try ditto.run()
        ditto.waitUntilExit()
        guard ditto.terminationStatus == 0 else {
            let msg = String(data: errPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            throw InstallError.unpackFailed(msg.isEmpty ? "ditto exit \(ditto.terminationStatus)" : msg)
        }
        try? fm.removeItem(at: zip)

        // Locate the tree root: GitHub zipballs wrap everything in one
        // heysami-Woven-<sha>/ dir; a git-archive asset may not.
        var root = unpackDir
        if !fm.fileExists(atPath: root + "/editor/serve.py") {
            let entries = (try? fm.contentsOfDirectory(atPath: unpackDir))?
                .filter { !$0.hasPrefix(".") || $0 == ".gitattributes" } ?? []
            let dirs = entries.filter { name in
                var isDir: ObjCBool = false
                return fm.fileExists(atPath: unpackDir + "/" + name, isDirectory: &isDir) && isDir.boolValue
            }
            if dirs.count == 1, fm.fileExists(atPath: unpackDir + "/" + dirs[0] + "/editor/serve.py") {
                root = unpackDir + "/" + dirs[0]
            } else {
                try? fm.removeItem(atPath: unpackDir)
                throw InstallError.unpackFailed("editor/serve.py not found in the archive")
            }
        }

        let tagDir = WovenPaths.installRoot + "/" + tag
        try? fm.removeItem(atPath: tagDir)
        try fm.moveItem(atPath: root, toPath: tagDir)
        if root != unpackDir { try? fm.removeItem(atPath: unpackDir) }

        try swapCurrent(to: tag)
    }

    /// current -> <tag> via symlink + POSIX rename(2), which atomically
    /// replaces an existing symlink (FileManager.moveItem refuses existing
    /// destinations, hence the raw calls).
    private func swapCurrent(to tag: String) throws {
        let tmp = WovenPaths.installRoot + "/.current.tmp"
        unlink(tmp)
        guard symlink(tag, tmp) == 0 else {
            throw InstallError.swapFailed("symlink: " + String(cString: strerror(errno)))
        }
        guard rename(tmp, WovenPaths.currentLink) == 0 else {
            unlink(tmp)
            throw InstallError.swapFailed("rename: " + String(cString: strerror(errno)))
        }
    }

    /// Keep the current target plus the newest 2 version dirs.
    private func prune() {
        let fm = FileManager.default
        guard let entries = try? fm.contentsOfDirectory(atPath: WovenPaths.installRoot) else { return }
        let currentTarget = (try? fm.destinationOfSymbolicLink(atPath: WovenPaths.currentLink)) ?? ""
        var versionDirs: [(name: String, mtime: Date)] = []
        for name in entries where name != "current" && !name.hasPrefix(".") {
            let full = WovenPaths.installRoot + "/" + name
            var isDir: ObjCBool = false
            guard fm.fileExists(atPath: full, isDirectory: &isDir), isDir.boolValue else { continue }
            let attrs = try? fm.attributesOfItem(atPath: full)
            let mtime = (attrs?[.modificationDate] as? Date) ?? Date.distantPast
            versionDirs.append((name, mtime))
        }
        let keep = Set(versionDirs.sorted { $0.mtime > $1.mtime }.prefix(2).map { $0.name } + [currentTarget])
        for (name, _) in versionDirs where !keep.contains(name) {
            try? fm.removeItem(atPath: WovenPaths.installRoot + "/" + name)
        }
    }
}

// MARK: - JSON date coding helpers

extension JSONEncoder {
    static func wovenDates() -> JSONEncoder {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        e.outputFormatting = [.prettyPrinted, .sortedKeys]
        return e
    }
}

extension JSONDecoder {
    static func wovenDates() -> JSONDecoder {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }
}
