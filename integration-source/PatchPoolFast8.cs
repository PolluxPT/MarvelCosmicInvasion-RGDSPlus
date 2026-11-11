using System;using System.IO;using System.Linq;using Mono.Cecil;using Mono.Cecil.Cil;
class PatchPoolFast8{
 static void Main(string[]args){
  var a=AssemblyDefinition.ReadAssembly(args[0]);var t=a.MainModule.Types.Single(x=>x.FullName=="Paris.Engine.Scene.GameObjectPoolManager");var original=t.Methods.Single(m=>m.Name=="orig_SpawnObject");var ensure=t.Methods.Single(m=>m.Name=="MCI_EnsureAvailable");
  var wrapper=t.Methods.Single(m=>m.Name=="SpawnObject"&&m.Parameters.Count==7);wrapper.Body=new MethodBody(wrapper);var wi=wrapper.Body.GetILProcessor();wi.Append(wi.Create(OpCodes.Ldarg_0));foreach(var p in wrapper.Parameters)wi.Append(wi.Create(OpCodes.Ldarg,p));wi.Append(wi.Create(OpCodes.Callvirt,original));wi.Append(wi.Create(OpCodes.Ret));
  var ins=original.Body.Instructions;var acquire=ins.First(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).Name=="AcquireLock");var lookup=acquire.Next;
  var exhausted=ins.Last(i=>i.OpCode==OpCodes.Brfalse&&i.Previous.OpCode==OpCodes.Ldloc_2);
  var missing=ins.First(i=>i.OpCode==OpCodes.Brfalse&&i.Previous.Operand is MethodReference&&((MethodReference)i.Previous.Operand).Name=="TryGetValue");

  // Reuse the context/editor references already in this module's locking method.
  var lockMethod=t.Methods.Single(m=>m.Name=="AcquireLock");
  var context=(MethodReference)lockMethod.Body.Instructions.First(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).Name=="get_Singleton").Operand;
  var editor=(MethodReference)lockMethod.Body.Instructions.First(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).Name=="get_EditorMode").Operand;
  var retried=new VariableDefinition(a.MainModule.TypeSystem.Boolean);original.Body.Variables.Add(retried);original.Body.InitLocals=true;var il=original.Body.GetILProcessor();
  foreach(var branch in new[]{exhausted,missing}){
   var fallback=(Instruction)branch.Operand;
   var block=new[]{il.Create(OpCodes.Ldloc,retried),il.Create(OpCodes.Brtrue,fallback),il.Create(OpCodes.Call,context),il.Create(OpCodes.Callvirt,editor),il.Create(OpCodes.Brtrue,fallback),il.Create(OpCodes.Ldc_I4_1),il.Create(OpCodes.Stloc,retried),il.Create(OpCodes.Ldarg_0),il.Create(OpCodes.Ldarg,original.Parameters[0]),il.Create(OpCodes.Ldarg,original.Parameters[2]),il.Create(OpCodes.Ldarg,original.Parameters[5]),il.Create(OpCodes.Ldarg,original.Parameters[6]),il.Create(OpCodes.Callvirt,ensure),il.Create(OpCodes.Br,lookup)};
   foreach(var i in block)il.InsertBefore(fallback,i);branch.Operand=block[0];
  }
  a.MainModule.Mvid=Guid.NewGuid();a.Write(args[0]+".new");File.Delete(args[0]);File.Move(args[0]+".new",args[0]);Console.WriteLine("Pool fast path: emergency construction only on failed selection, one bounded retry, original spawn selection retained.");
 }
}
