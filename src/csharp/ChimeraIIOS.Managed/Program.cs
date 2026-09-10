using System.Numerics;
using System.Text.Json;
using ChimeraIIOS.Managed;

var a = new BigInteger(42);
var b = new BigInteger(7);
var c = a + b;
Console.WriteLine("Chimera II host research scaffold");
Console.WriteLine($"8192-bit register word0={c}");
Console.WriteLine(JsonSerializer.Serialize(ChimeraRuntime.Health()));
