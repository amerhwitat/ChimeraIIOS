import Foundation
public struct ServiceDescriptor: Codable { public let id:String; public let platform:String; public let backend:String; public let capabilities:[String]; public init(id:String,platform:String,backend:String,capabilities:[String]){self.id=id;self.platform=platform;self.backend=backend;self.capabilities=capabilities} }
