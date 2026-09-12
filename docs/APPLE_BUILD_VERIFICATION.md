# Apple build verification

## Source verification completed

- Added XcodeGen `project.yml` specifications and SwiftUI entrypoints to the portfolio Apple application boundaries.
- Added macOS GitHub Actions validation workflows using `macos-latest`, Homebrew XcodeGen and `xcodebuild` simulator builds.
- Added archive/export scripts using `xcodebuild` and optional fastlane lanes for BizX/BizXtreme.
- Added macOS prerequisite automation for Xcode, Swift, XcodeGen and optional fastlane.
- Added Windows PowerShell/CMD orchestration that explicitly refuses to claim local iOS compilation without a macOS host.

## Verification status

Repository files were inspected through GitHub after creation. A macOS/Xcode runner is required to execute the actual Apple compiler and IPA exporter. This environment did not execute Xcode, so no IPA binary is claimed as built by this session.

## Expected macOS validation

```bash
brew install xcodegen
xcodegen generate --spec apple/project.yml
xcodebuild -project apple/ChimeraIIOSApple.xcodeproj -scheme ChimeraIIOSApple -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build
```

For a signed IPA, archive the device target and export with a real `ExportOptions.plist` and operator-controlled signing credentials. Never commit those credentials.

## Open-source automation

XcodeGen provides reproducible project generation from YAML/JSON specifications. fastlane provides MIT-licensed automation around Xcode build/archive/export. Both remain wrappers around Apple's required macOS/Xcode toolchain.
