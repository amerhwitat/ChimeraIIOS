// Swift Package Manager boundary for Apple-shared source.
// Application targets remain native Xcode projects when an IPA/app target is required.
// This package intentionally has no third-party dependency.
import PackageDescription

let package = Package(
    name: "ChimeraAppleShared",
    platforms: [.iOS(.v16), .macOS(.13)],
    products: [.library(name: "ChimeraAppleShared", targets: ["ChimeraAppleShared"])],
    targets: [.target(name: "ChimeraAppleShared", path: "Shared/Sources")]
)
