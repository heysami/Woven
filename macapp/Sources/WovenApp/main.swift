import AppKit

// Plain main.swift bootstrap (no @main): create the shared application,
// attach the delegate, run. LSUIElement=true in Info.plist makes the app
// start as a menubar agent; AppDelegate flips activation policy to .regular
// while an editor window is open.
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
