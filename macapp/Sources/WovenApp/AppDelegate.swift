import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {

    private var statusMenu: StatusMenuController!
    private var installManager: InstallManager!
    private var daemonManager: DaemonManager?
    private var setupWindow: SetupWindowController?
    private var pythonPath: String?

    // MARK: - Launch

    func applicationDidFinishLaunching(_ notification: Notification) {
        buildMainMenu()
        statusMenu = StatusMenuController(actions: menuActions())
        WebWindowController.onWindowCountChange = { [weak self] in
            self?.updateActivationPolicy()
        }

        // 1. Command Line Tools gate. Never touch /usr/bin/python3 before
        //    this: on a Mac without CLT the shim pops Apple's installer
        //    dialog at an uncontrolled moment.
        guard EnvProbe.cltInstalled() else {
            promptCLTInstall()
            return
        }

        // 2. python3 >= 3.9 (mirrors editor/serve.command's find_python).
        guard let python = EnvProbe.resolvePython() else {
            fatalAlert(title: "Python 3.9+ not found",
                       message: "Woven needs Python 3.9 or newer and none was found on this Mac.\n\nInstall one from python.org (or: brew install python@3.12), then open Woven again.")
            return
        }
        pythonPath = python

        // 3. Woven files: reuse the installed tree, or first-run download.
        installManager = InstallManager()
        if installManager.isInstalled {
            startDaemon()
            installManager.backgroundCheck { [weak self] _ in
                // Update swapped in silently; the menu shows the restart hint
                // via updateReadyText. Never auto-restart: in-flight agent
                // runs + tunnels must not be killed.
                _ = self
            }
        } else {
            runFirstInstall()
        }
    }

    private func runFirstInstall() {
        let setup = SetupWindowController()
        setupWindow = setup
        setup.update(fraction: -1, text: "Checking the latest Woven release...")
        setup.present()

        installManager.resolveLatestRelease { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .failure(let err):
                self.installErrorRetry(message: err.localizedDescription)
            case .success(let release):
                self.installManager.install(release: release, progress: { frac, text in
                    self.setupWindow?.update(fraction: frac, text: text)
                }) { r in
                    switch r {
                    case .failure(let err):
                        self.installErrorRetry(message: err.localizedDescription)
                    case .success:
                        self.setupWindow?.dismiss()
                        self.setupWindow = nil
                        self.startDaemon()
                    }
                }
            }
        }
    }

    private func installErrorRetry(message: String) {
        setupWindow?.dismiss()
        let a = NSAlert()
        a.messageText = "Could not download Woven"
        a.informativeText = message
        a.addButton(withTitle: "Retry")
        a.addButton(withTitle: "Quit")
        if a.runModal() == .alertFirstButtonReturn {
            runFirstInstall()
        } else {
            NSApp.terminate(nil)
        }
    }

    // MARK: - Daemon

    private func startDaemon() {
        guard let python = pythonPath else { return }
        // A freshly started daemon always serves the `current` tree, which
        // already contains any downloaded update - the restart hint is stale.
        installManager.updateReadyTag = nil
        // The daemon silently falls back to single-project mode when
        // TH_WORKSPACE_DIR does not exist, so create it first.
        try? FileManager.default.createDirectory(atPath: WovenPaths.workspaceDir,
                                                 withIntermediateDirectories: true)
        let dm = DaemonManager(pythonPath: python)
        daemonManager = dm
        dm.onReady = { [weak self] in
            self?.openEditorWindow()
            // Self-heal the tree-local services (shader-verify, cloudflared,
            // glslang, rembg) - a fresh or updated tree may lack them and the
            // onboarding auto-installer only runs when its wizard is visible.
            self?.daemonManager?.ensureLocalServices()
        }
        dm.onStateChange = { [weak self] in
            if case .failed(let msg) = self?.daemonManager?.state {
                self?.fatalAlert(title: "Woven daemon problem", message: msg, terminate: false)
            }
        }
        dm.start()
    }

    private func openEditorWindow() {
        WebWindowController.openMain(url: WovenPaths.editorURL)
        updateActivationPolicy()
    }

    private func updateActivationPolicy() {
        let hasWindows = WebWindowController.openWindowCount > 0 || setupWindow != nil
        NSApp.setActivationPolicy(hasWindows ? .regular : .accessory)
    }

    // MARK: - Main menu

    /// cmd+C/V/X/A/Z are NOT raw key events on macOS - they are key
    /// equivalents dispatched through the main menu's Edit items to the first
    /// responder (the WKWebView). A programmatic app has no menu unless it
    /// builds one, so without this none of the standard edit shortcuts work
    /// in the editor. (Page-level shortcuts like cmd+K/cmd+F are handled by
    /// the editor's own JS and never needed the menu.)
    private func buildMainMenu() {
        let main = NSMenu()

        let appItem = NSMenuItem()
        main.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About Woven",
                        action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)),
                        keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide Woven",
                        action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit Woven",
                        action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu

        let editItem = NSMenuItem()
        main.addItem(editItem)
        let edit = NSMenu(title: "Edit")
        edit.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        let redo = NSMenuItem(title: "Redo", action: Selector(("redo:")), keyEquivalent: "z")
        redo.keyEquivalentModifierMask = [.command, .shift]
        edit.addItem(redo)
        edit.addItem(.separator())
        edit.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = edit

        let windowItem = NSMenuItem()
        main.addItem(windowItem)
        let windowMenu = NSMenu(title: "Window")
        windowMenu.addItem(withTitle: "Close Window",
                           action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        windowMenu.addItem(withTitle: "Minimize",
                           action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        windowMenu.addItem(withTitle: "Zoom",
                           action: #selector(NSWindow.performZoom(_:)), keyEquivalent: "")
        windowItem.submenu = windowMenu
        NSApp.windowsMenu = windowMenu

        NSApp.mainMenu = main
    }

    // MARK: - Menu actions

    private func menuActions() -> StatusMenuController.Actions {
        StatusMenuController.Actions(
            openWoven: { [weak self] in
                guard let self = self else { return }
                if self.daemonManager?.isServing == true {
                    self.openEditorWindow()
                } else if self.daemonManager == nil, self.installManager?.isInstalled == true {
                    self.startDaemon()
                } else if case .failed = self.daemonManager?.state ?? .idle {
                    self.daemonManager?.start()
                }
            },
            restartDaemon: { [weak self] in
                guard let self = self, let dm = self.daemonManager else { return }
                if dm.state == .attached {
                    let a = NSAlert()
                    a.messageText = "Take over the running daemon?"
                    a.informativeText = "A Woven daemon you started yourself (for example in Terminal) is serving port \(dm.port). Restarting from here will replace it with one managed by the app."
                    a.addButton(withTitle: "Take Over")
                    a.addButton(withTitle: "Cancel")
                    guard a.runModal() == .alertFirstButtonReturn else { return }
                }
                self.installManager.updateReadyTag = nil
                dm.restart()
            },
            checkForUpdates: { [weak self] in self?.manualUpdateCheck() },
            openWorkspace: {
                NSWorkspace.shared.open(URL(fileURLWithPath: WovenPaths.workspaceDir))
            },
            revealFiles: {
                NSWorkspace.shared.activateFileViewerSelecting(
                    [URL(fileURLWithPath: WovenPaths.currentLink)])
            },
            viewLog: {
                NSWorkspace.shared.open(URL(fileURLWithPath: WovenPaths.daemonLog))
            },
            quit: {
                NSApp.terminate(nil)
            },
            daemonStatusText: { [weak self] in
                guard let dm = self?.daemonManager else { return "Daemon: not started" }
                switch dm.state {
                case .idle: return "Daemon: stopped"
                case .probing: return "Daemon: checking port \(dm.port)..."
                case .starting: return "Daemon: starting..."
                case .running: return "Daemon: running (managed, :\(dm.port))"
                case .attached: return "Daemon: running (attached, :\(dm.port))"
                case .failed: return "Daemon: stopped - see log"
                }
            },
            fetchShares: { [weak self] completion in
                if let dm = self?.daemonManager {
                    dm.fetchShares(completion: completion)
                } else {
                    completion([])
                }
            },
            updateReadyText: { [weak self] in
                guard let tag = self?.installManager?.updateReadyTag else { return nil }
                return "Update \(tag) ready - Restart Daemon to apply"
            }
        )
    }

    private func manualUpdateCheck() {
        installManager.resolveLatestRelease { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .failure(let err):
                self.fatalAlert(title: "Update check failed", message: err.localizedDescription, terminate: false)
            case .success(let release):
                if release.tag == self.installManager.state.installedTag {
                    let a = NSAlert()
                    a.messageText = "Woven is up to date"
                    a.informativeText = "Installed: \(release.tag)"
                    a.runModal()
                    return
                }
                let setup = SetupWindowController(title: "Updating Woven")
                self.setupWindow = setup
                setup.update(fraction: -1, text: "Downloading Woven \(release.tag)...")
                setup.present()
                self.installManager.install(release: release, progress: { frac, text in
                    setup.update(fraction: frac, text: text)
                }) { r in
                    setup.dismiss()
                    self.setupWindow = nil
                    self.updateActivationPolicy()
                    switch r {
                    case .failure(let err):
                        self.fatalAlert(title: "Update failed", message: err.localizedDescription, terminate: false)
                    case .success:
                        self.installManager.updateReadyTag = release.tag
                        let a = NSAlert()
                        a.messageText = "Update \(release.tag) installed"
                        a.informativeText = "The files are in place. Use Restart Daemon (menubar) to switch to the new version - any running agent builds and share links survive until then."
                        a.runModal()
                    }
                }
            }
        }
    }

    // MARK: - Quit

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard let dm = daemonManager, dm.ownsDaemon else { return .terminateNow }
        dm.stopForQuit {
            NSApp.reply(toApplicationShouldTerminate: true)
        }
        return .terminateLater
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !flag, daemonManager?.isServing == true {
            openEditorWindow()
        }
        return true
    }

    // MARK: - Alerts

    private func promptCLTInstall() {
        let a = NSAlert()
        a.messageText = "Woven needs Python 3"
        a.informativeText = "Python 3 ships with Apple's Command Line Tools, which are not installed yet.\n\nClick Install and accept Apple's dialog; when it finishes, open Woven again."
        a.addButton(withTitle: "Install...")
        a.addButton(withTitle: "Quit")
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        if a.runModal() == .alertFirstButtonReturn {
            EnvProbe.offerCLTInstall()
        }
        NSApp.terminate(nil)
    }

    private func fatalAlert(title: String, message: String, terminate: Bool = true) {
        NSApp.activate(ignoringOtherApps: true)
        let a = NSAlert()
        a.messageText = title
        a.informativeText = message
        a.runModal()
        if terminate { NSApp.terminate(nil) }
    }
}
