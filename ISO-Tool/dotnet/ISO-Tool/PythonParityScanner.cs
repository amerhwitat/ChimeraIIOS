using System.IO;
namespace Chimera.IsoTool;
public static class PythonParityScanner { public static IEnumerable<string> Scan(string root)=>Directory.Exists(root)?Directory.EnumerateFiles(root,"*.py",SearchOption.AllDirectories):Enumerable.Empty<string>(); }
