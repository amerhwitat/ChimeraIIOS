# Apple build tools

These scripts prepare and validate the portfolio's Apple source tree.

`install-apple-toolchain.sh` checks macOS/Xcode/Swift and optional fastlane.

`build-apple-portfolio.sh` validates Swift packages and discovers Apple projects.

`build-apple-portfolio.ps1` and `.cmd` are Windows orchestration wrappers; actual iOS IPA compilation requires macOS/Xcode.

For a real product, use the repository's `apple/scripts/archive-ios.sh` followed by `export-ipa.sh` on a macOS runner with operator-controlled signing.
