using System;using System.IO;using System.Linq;using Mono.Cecil;using Mono.Cecil.Cil;
class PatchSession{
 public static void Main(string[] args){
  var r=new DefaultAssemblyResolver();r.AddSearchDirectory(Path.GetDirectoryName(args[0]));r.AddSearchDirectory(args[2]);
  var a=AssemblyDefinition.ReadAssembly(args[0],new ReaderParameters{AssemblyResolver=r});
  var m=a.EntryPoint;if(m==null||!m.HasBody||m.ReturnType.FullName!="System.Void")throw new Exception("Unexpected entry point");
  var ret=m.Body.Instructions.Last();if(ret.OpCode!=OpCodes.Ret)throw new Exception("Unexpected entry-point end");
  if(m.Body.Instructions.Any(i=>i.OpCode==OpCodes.Ldstr&&(i.Operand as string)=="RGDS_EXIT: game disposal complete; closing session"))throw new Exception("Already patched");
  var il=m.Body.GetILProcessor();ret.OpCode=OpCodes.Ldstr;ret.Operand="RGDS_EXIT: game disposal complete; closing session";
  il.Append(il.Create(OpCodes.Call,a.MainModule.ImportReference(typeof(Console).GetMethod("WriteLine",new[]{typeof(string)}))));
  il.Append(il.Create(OpCodes.Ldc_I4_0));il.Append(il.Create(OpCodes.Call,a.MainModule.ImportReference(typeof(Environment).GetMethod("Exit",new[]{typeof(int)}))));il.Append(il.Create(OpCodes.Ret));
  a.MainModule.Mvid=Guid.NewGuid();a.Write(args[1]);Console.WriteLine("Patched normal entry-point completion after game disposal: "+m.FullName);
 }
}
