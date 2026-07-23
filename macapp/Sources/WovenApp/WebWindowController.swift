import AppKit
import WebKit

/// An NSWindow hosting a WKWebView pointed at the local editor (or a child
/// page). Routing policy:
///   - localhost / 127.0.0.1 / blob: / about: -> stays in-app (new child
///     window for window.open/target=_blank)
///   - everything else (github.com, brew.sh, provider docs, trycloudflare
///     share links) -> the user's default browser
/// Downloads (<a download>, blob exports, non-renderable responses) land in
/// ~/Downloads via WKDownloadDelegate.
final class WebWindowController: NSWindowController, WKUIDelegate, WKNavigationDelegate, WKDownloadDelegate, NSWindowDelegate {

    /// Retains open windows (isReleasedWhenClosed = false + this registry).
    private(set) static var registry = Set<WebWindowController>()
    static var openWindowCount: Int { registry.count }
    private(set) static weak var main: WebWindowController?

    /// Called whenever a window opens or closes, so the app can flip its
    /// activation policy between .regular and .accessory.
    static var onWindowCountChange: (() -> Void)?

    private var webView: WKWebView!
    private let isMain: Bool
    /// True while the last main-frame load failed (daemon down); openMain
    /// uses it to reload instead of focusing a dead page.
    private var provisionalFailed = false

    // MARK: - Shared configuration
    // (No WKProcessPool wrangling: since macOS 12 all WKWebViews share one
    // web-content process pool automatically.)

    static func makeConfiguration() -> WKWebViewConfiguration {
        let cfg = WKWebViewConfiguration()
        cfg.websiteDataStore = .default() // persistent: editor localStorage survives relaunch
        cfg.preferences.setValue(true, forKey: "developerExtrasEnabled") // right-click > Inspect Element
        // Append "Woven/1" to the UA so the editor can tell it is running
        // inside the app shell (isWovenDesktopShell in app.js) and swap
        // terminal-flavored instructions for menu-bar ones. Child windows
        // inherit this via the opener-derived configuration.
        cfg.applicationNameForUserAgent = "Woven/1"
        return cfg
    }

    // MARK: - Creation

    static func openMain(url: URL) {
        NSLog("[woven] openMain: \(url)")
        if let existing = main {
            // Recover a dead page: after a daemon crash + restart the window
            // is showing a connection error; reload instead of just focusing.
            if existing.provisionalFailed || existing.webView.url == nil {
                existing.provisionalFailed = false
                existing.webView.load(URLRequest(url: url))
            }
            existing.showWindow(nil)
            existing.window?.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }
        let wc = WebWindowController(configuration: makeConfiguration(), isMain: true)
        main = wc
        wc.webView.load(URLRequest(url: url))
        wc.present()
    }

    /// Child window creation for createWebViewWith: MUST use the exact
    /// configuration WebKit hands us (blob: URLs are scoped to the opener's
    /// process; WebKit also asserts on a mismatched configuration).
    private static func openChild(configuration: WKWebViewConfiguration) -> WKWebView {
        let wc = WebWindowController(configuration: configuration, isMain: false)
        wc.present()
        return wc.webView
    }

    private init(configuration: WKWebViewConfiguration, isMain: Bool) {
        self.isMain = isMain
        let rect = NSRect(x: 0, y: 0, width: isMain ? 1360 : 1100, height: isMain ? 860 : 760)
        let window = NSWindow(contentRect: rect,
                              styleMask: [.titled, .closable, .miniaturizable, .resizable],
                              backing: .buffered, defer: false)
        window.title = "Woven"
        window.minSize = NSSize(width: 900, height: 600)
        window.isReleasedWhenClosed = false
        window.center()
        super.init(window: window)
        window.delegate = self

        let wv = WKWebView(frame: rect, configuration: configuration)
        wv.uiDelegate = self
        wv.navigationDelegate = self
        wv.allowsMagnification = true
        window.contentView = wv
        webView = wv

        if isMain {
            window.setFrameAutosaveName("WovenEditor")
        }
        Self.registry.insert(self)
        Self.onWindowCountChange?()
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { fatalError("not used") }

    private func present() {
        showWindow(nil)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    // MARK: - Internal/external routing

    /// URLs that belong inside the app window(s).
    static func isInternal(_ url: URL) -> Bool {
        switch url.scheme?.lowercased() {
        case "blob", "about", "data": return true
        default: break
        }
        switch url.host?.lowercased() {
        case "localhost", "127.0.0.1", "::1", "[::1]": return true
        default: return false
        }
    }

    // MARK: - WKUIDelegate

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url, !url.absoluteString.isEmpty,
           url.absoluteString != "about:blank", !Self.isInternal(url) {
            NSWorkspace.shared.open(url)
            return nil
        }
        // Internal (or blank window.open the page will drive via JS):
        // in-app child window. WebKit loads the request into the returned view.
        return Self.openChild(configuration: configuration)
    }

    func webViewDidClose(_ webView: WKWebView) {
        window?.close()
    }

    // File chooser: like alert/confirm, WKWebView renders NOTHING for
    // <input type="file"> unless the host supplies the panel - attachments
    // (chat, DS node references, uploads) silently no-op without this.
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = parameters.allowsDirectories
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.resolvesAliases = true
        if let window = self.window {
            panel.beginSheetModal(for: window) { resp in
                completionHandler(resp == .OK ? panel.urls : nil)
            }
        } else {
            completionHandler(panel.runModal() == .OK ? panel.urls : nil)
        }
    }

    // JS dialogs: WKWebView renders NOTHING for alert/confirm/prompt by
    // default and the editor uses them (uiAlert wrappers still funnel here
    // in fallback paths).
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert()
        a.messageText = "Woven"
        a.informativeText = message
        a.runModal()
        completionHandler()
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert()
        a.messageText = "Woven"
        a.informativeText = message
        a.addButton(withTitle: "OK")
        a.addButton(withTitle: "Cancel")
        completionHandler(a.runModal() == .alertFirstButtonReturn)
    }

    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String,
                 defaultText: String?, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping (String?) -> Void) {
        let a = NSAlert()
        a.messageText = "Woven"
        a.informativeText = prompt
        a.addButton(withTitle: "OK")
        a.addButton(withTitle: "Cancel")
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 260, height: 24))
        field.stringValue = defaultText ?? ""
        a.accessoryView = field
        completionHandler(a.runModal() == .alertFirstButtonReturn ? field.stringValue : nil)
    }

    // MARK: - WKNavigationDelegate

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if navigationAction.shouldPerformDownload {
            decisionHandler(.download)
            return
        }
        // Only hijack explicit main-frame link clicks to external hosts.
        // Subresources and iframe content (Google Fonts, CDNs inside
        // generated prototypes) must load normally.
        if let url = navigationAction.request.url,
           navigationAction.navigationType == .linkActivated,
           navigationAction.targetFrame?.isMainFrame ?? false,
           !Self.isInternal(url) {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(navigationResponse.canShowMIMEType ? .allow : .download)
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.delegate = self
    }

    // MARK: - WKDownloadDelegate

    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse,
                  suggestedFilename: String,
                  completionHandler: @escaping (URL?) -> Void) {
        let downloads = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory() + "/Downloads")
        let name = suggestedFilename.isEmpty ? "download" : suggestedFilename
        var dest = downloads.appendingPathComponent(name)
        let base = (name as NSString).deletingPathExtension
        let ext = (name as NSString).pathExtension
        var n = 2
        while FileManager.default.fileExists(atPath: dest.path) {
            let numbered = ext.isEmpty ? "\(base) (\(n))" : "\(base) (\(n)).\(ext)"
            dest = downloads.appendingPathComponent(numbered)
            n += 1
        }
        lastDownloadDestination = dest
        completionHandler(dest)
    }

    private var lastDownloadDestination: URL?

    func downloadDidFinish(_ download: WKDownload) {
        if let dest = lastDownloadDestination {
            NSWorkspace.shared.activateFileViewerSelecting([dest])
        }
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        let a = NSAlert()
        a.messageText = "Download failed"
        a.informativeText = error.localizedDescription
        a.runModal()
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        NSLog("[woven] provisional navigation failed: \(error)")
        provisionalFailed = true
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        NSLog("[woven] navigation failed: \(error)")
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        NSLog("[woven] navigation finished: \(webView.url?.absoluteString ?? "?")")
        provisionalFailed = false
    }

    // MARK: - NSWindowDelegate

    func windowWillClose(_ notification: Notification) {
        webView.stopLoading()
        Self.registry.remove(self)
        if Self.main === self { Self.main = nil }
        Self.onWindowCountChange?()
    }
}
