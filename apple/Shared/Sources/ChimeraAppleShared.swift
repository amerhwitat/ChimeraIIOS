import Foundation

public struct ChimeraAppleBuildInfo: Sendable, Codable {
    public let platform: String
    public let schemaVersion: Int

    public init(platform: String, schemaVersion: Int = 1) {
        self.platform = platform
        self.schemaVersion = schemaVersion
    }
}

public enum ChimeraAppleRuntime {
    public static var buildInfo: ChimeraAppleBuildInfo {
        #if os(iOS)
        return .init(platform: "iOS")
        #elseif os(macOS)
        return .init(platform: "macOS")
        #else
        return .init(platform: "Apple")
        #endif
    }
}
