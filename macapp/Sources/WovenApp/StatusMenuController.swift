import AppKit

/// The menubar surface. All actions are forwarded to the AppDelegate via
/// the Actions closure bundle; state is re-read in menuWillOpen (no polling).
final class StatusMenuController: NSObject, NSMenuDelegate {

    struct Actions {
        var openWoven: () -> Void
        var restartDaemon: () -> Void
        var checkForUpdates: () -> Void
        var openWorkspace: () -> Void
        var revealFiles: () -> Void
        var viewLog: () -> Void
        var quit: () -> Void
        var daemonStatusText: () -> String
        var fetchShares: (@escaping ([DaemonManager.ShareLink]) -> Void) -> Void
        var updateReadyText: () -> String?
    }

    private let statusItem: NSStatusItem
    private let menu = NSMenu()
    private let actions: Actions

    private let statusLine = NSMenuItem(title: "Daemon: starting...", action: nil, keyEquivalent: "")
    private let updateLine = NSMenuItem(title: "", action: nil, keyEquivalent: "")
    private let sharesItem = NSMenuItem(title: "Share Links", action: nil, keyEquivalent: "")

    init(actions: Actions) {
        self.actions = actions
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        super.init()

        if let button = statusItem.button {
            // The Woven logogram as a template image (1x + 2x reps bundled by
            // build.sh); macOS tints it to match the menu bar. Fall back to
            // the old SF Symbol if the resources are missing.
            var img: NSImage?
            if let base = Bundle.main.image(forResource: "woven-mark-18") {
                let mark = NSImage(size: NSSize(width: 18, height: 18))
                for rep in base.representations { mark.addRepresentation(rep) }
                if let hi = Bundle.main.image(forResource: "woven-mark-36") {
                    for rep in hi.representations {
                        rep.size = NSSize(width: 18, height: 18)   // 2x rep
                        mark.addRepresentation(rep)
                    }
                }
                img = mark
            } else {
                img = NSImage(systemSymbolName: "w.circle.fill", accessibilityDescription: "Woven")
            }
            img?.isTemplate = true
            button.image = img
        }

        menu.delegate = self
        buildMenu()
        statusItem.menu = menu
    }

    private func buildMenu() {
        let open = NSMenuItem(title: "Open Woven", action: #selector(onOpen), keyEquivalent: "o")
        open.target = self
        menu.addItem(open)

        statusLine.isEnabled = false
        menu.addItem(statusLine)

        updateLine.isEnabled = false
        updateLine.isHidden = true
        menu.addItem(updateLine)

        sharesItem.submenu = NSMenu()
        sharesItem.isHidden = true
        menu.addItem(sharesItem)

        menu.addItem(.separator())

        let restart = NSMenuItem(title: "Restart Daemon", action: #selector(onRestart), keyEquivalent: "")
        restart.target = self
        menu.addItem(restart)

        let update = NSMenuItem(title: "Check for Updates...", action: #selector(onCheckUpdates), keyEquivalent: "")
        update.target = self
        menu.addItem(update)

        menu.addItem(.separator())

        let workspace = NSMenuItem(title: "Open Workspace Folder", action: #selector(onWorkspace), keyEquivalent: "")
        workspace.target = self
        menu.addItem(workspace)

        let reveal = NSMenuItem(title: "Reveal Woven Files in Finder", action: #selector(onReveal), keyEquivalent: "")
        reveal.target = self
        menu.addItem(reveal)

        let log = NSMenuItem(title: "View Daemon Log", action: #selector(onLog), keyEquivalent: "")
        log.target = self
        menu.addItem(log)

        menu.addItem(.separator())

        let quit = NSMenuItem(title: "Quit Woven", action: #selector(onQuit), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)
    }

    // MARK: - NSMenuDelegate

    func menuWillOpen(_ menu: NSMenu) {
        statusLine.title = actions.daemonStatusText()
        if let hint = actions.updateReadyText() {
            updateLine.title = hint
            updateLine.isHidden = false
        } else {
            updateLine.isHidden = true
        }
        // Lazy share fetch with a tight timeout; rebuild the submenu when it
        // answers (the menu is already open; item updates on main are fine).
        sharesItem.isHidden = true
        actions.fetchShares { [weak self] links in
            guard let self = self, !links.isEmpty else { return }
            let sub = NSMenu()
            for link in links {
                let item = NSMenuItem(title: "\(link.label): \(link.url)", action: #selector(self.onCopyShare(_:)), keyEquivalent: "")
                item.target = self
                item.representedObject = link.url
                sub.addItem(item)
            }
            self.sharesItem.submenu = sub
            self.sharesItem.isHidden = false
        }
    }

    // MARK: - Actions

    @objc private func onOpen() { actions.openWoven() }
    @objc private func onRestart() { actions.restartDaemon() }
    @objc private func onCheckUpdates() { actions.checkForUpdates() }
    @objc private func onWorkspace() { actions.openWorkspace() }
    @objc private func onReveal() { actions.revealFiles() }
    @objc private func onLog() { actions.viewLog() }
    @objc private func onQuit() { actions.quit() }

    @objc private func onCopyShare(_ sender: NSMenuItem) {
        guard let url = sender.representedObject as? String else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(url, forType: .string)
    }
}
