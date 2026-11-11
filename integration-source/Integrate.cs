using System;using System.Linq;using Mono.Cecil;using Mono.Cecil.Cil;
class Integrate {
 static void Main(string[] args){
  string dir=args[0];var resolver=new DefaultAssemblyResolver();resolver.AddSearchDirectory(dir);resolver.AddSearchDirectory("marvel-host-root/usr/lib/mono/4.5");
  var rp=new ReaderParameters{AssemblyResolver=resolver};var fna=AssemblyDefinition.ReadAssembly(System.IO.Path.Combine(dir,"FNA.dll"),rp);var sdk=AssemblyDefinition.ReadAssembly(System.IO.Path.Combine(dir,"RGDS.dll"),rp);
  var game=fna.MainModule.Types.Single(t=>t.FullName=="Microsoft.Xna.Framework.Game");var tick=game.Methods.Single(m=>m.Name=="Tick"&&m.HasBody&&m.Parameters.Count==0);
  var frame=sdk.MainModule.Types.Single(t=>t.FullName=="RGDS.Handheld").Methods.Single(m=>m.Name=="Frame");var reference=fna.MainModule.ImportReference(frame);var il=tick.Body.GetILProcessor();var first=tick.Body.Instructions[0];il.InsertBefore(first,il.Create(OpCodes.Ldarg_0));il.InsertBefore(first,il.Create(OpCodes.Call,reference));
  fna.Write(System.IO.Path.Combine(dir,"FNA.integrated.dll"));Console.WriteLine("Integrated normal exit into FNA Game.Tick.");
 }
}
