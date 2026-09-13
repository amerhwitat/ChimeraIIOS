import Foundation
public enum ChimeraDirection { case ltr, rtl }
public struct ChimeraLocale { public let id: String; public let language: String; public let script: String; public let direction: ChimeraDirection
  public static func from(_ id: String?) -> ChimeraLocale { if id?.lowercased().hasPrefix("ar") == true { return ChimeraLocale(id:"ar-SA",language:"ar",script:"Arabic",direction:.rtl) }; return ChimeraLocale(id:"en-US",language:"en",script:"Latin",direction:.ltr) }
}
