// swift-tools-version:5.9
// Woven.app - native menubar launcher for the Woven daemon + editor.
// Built with Command Line Tools only (no Xcode project); build.sh assembles
// the .app bundle around the SPM-built executable.
import PackageDescription

let package = Package(
    name: "WovenApp",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "WovenApp", path: "Sources/WovenApp")
    ]
)
