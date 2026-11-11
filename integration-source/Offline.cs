using System;using System.IO;using System.Linq;using Mono.Cecil;using Mono.Cecil.Cil;
class Offline {
 static void Main(string[] a){var resolver=new DefaultAssemblyResolver();resolver.AddSearchDirectory(Path.GetDirectoryName(a[0]));resolver.AddSearchDirectory("marvel-host-root/usr/lib/mono/4.5");var g=AssemblyDefinition.ReadAssembly(a[0],new ReaderParameters{AssemblyResolver=resolver});var module=g.MainModule;var main=module.Types.Single(t=>t.FullName=="Paris.Program").Methods.Single(m=>m.Name=="Main");var ins=main.Body.Instructions;
 int first=ins.ToList().FindIndex(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).FullName.Contains("NBug.Settings::set_ReleaseMode"))-1;
 int last=ins.ToList().FindIndex(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).FullName.Contains("NBug.Handler::get_UnhandledException"))+1;
 if(first<0||last<=first)throw new Exception("Unexpected reporting registration layout");
 for(int n=first;n<=last;n++){ins[n].OpCode=OpCodes.Nop;ins[n].Operand=null;}
 foreach(var t in module.Types.Where(t=>t.FullName=="Paris.DiscordWebHook"||t.FullName=="Paris.FormUpload"||t.FullName=="Paris.NBugDiscordProtocol"))foreach(var m in t.Methods.Where(m=>m.HasBody&&m.Name!=".ctor")){
 if(m.ReturnType.FullName=="System.String"||m.ReturnType.FullName=="System.Net.HttpWebResponse"||m.ReturnType.FullName=="System.Boolean"||m.ReturnType.FullName=="System.Void"){
 m.Body=new MethodBody(m);var il=m.Body.GetILProcessor();if(m.ReturnType.FullName=="System.Boolean")il.Append(il.Create(OpCodes.Ldc_I4_0));else if(m.ReturnType.FullName!="System.Void")il.Append(il.Create(OpCodes.Ldnull));il.Append(il.Create(OpCodes.Ret));Console.WriteLine("Local-only: "+m.FullName);}}
 // The desktop game kills itself after normal return, bypassing cleanup. Return normally.
 for(int n=0;n+1<ins.Count;n++)if(ins[n].Operand is MethodReference&&((MethodReference)ins[n].Operand).FullName=="System.Diagnostics.Process System.Diagnostics.Process::GetCurrentProcess()"&&ins[n+1].Operand is MethodReference&&((MethodReference)ins[n+1].Operand).Name=="Kill"){
 ins[n].OpCode=OpCodes.Nop;ins[n].Operand=null;ins[n+1].OpCode=OpCodes.Nop;ins[n+1].Operand=null;}
 g.Write(a[1]);Console.WriteLine("Removed crash-report registration and external uploads; normal exit retained.");
 }
}
