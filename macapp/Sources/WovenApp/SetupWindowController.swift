import AppKit

/// Small first-run window: "Downloading Woven vX.Y.Z..." with a progress bar.
/// Also reused for manual update downloads triggered from the menu.
final class SetupWindowController: NSWindowController {

    private let label = NSTextField(labelWithString: "Preparing...")
    private let bar = NSProgressIndicator()

    init(title: String = "Setting up Woven") {
        let rect = NSRect(x: 0, y: 0, width: 440, height: 120)
        let window = NSWindow(contentRect: rect,
                              styleMask: [.titled],
                              backing: .buffered, defer: false)
        window.title = title
        window.isReleasedWhenClosed = false
        window.center()
        super.init(window: window)

        let content = NSView(frame: rect)
        label.frame = NSRect(x: 24, y: 66, width: 392, height: 20)
        label.lineBreakMode = .byTruncatingMiddle
        content.addSubview(label)

        bar.frame = NSRect(x: 24, y: 34, width: 392, height: 20)
        bar.minValue = 0
        bar.maxValue = 1
        bar.isIndeterminate = true
        bar.style = .bar
        bar.startAnimation(nil)
        content.addSubview(bar)

        window.contentView = content
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { fatalError("not used") }

    func present() {
        showWindow(nil)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    /// fraction < 0 (or unknown totals) shows an indeterminate bar.
    func update(fraction: Double, text: String) {
        label.stringValue = text
        if fraction >= 0 {
            if bar.isIndeterminate {
                bar.isIndeterminate = false
                bar.stopAnimation(nil)
            }
            bar.doubleValue = fraction
        } else if !bar.isIndeterminate {
            bar.isIndeterminate = true
            bar.startAnimation(nil)
        }
    }

    func dismiss() {
        window?.orderOut(nil)
    }
}
