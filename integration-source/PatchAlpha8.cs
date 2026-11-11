using System;using System.IO;using System.Linq;using Mono.Cecil;using Mono.Cecil.Cil;
class PatchAlpha8{
 static MethodDefinition Method(AssemblyDefinition a,string type,string method){return a.MainModule.Types.Single(t=>t.FullName==type).Methods.Single(m=>m.Name==method&&m.HasBody);}
 static void LongBranches(MethodDefinition m){foreach(var i in m.Body.Instructions){switch(i.OpCode.Code){case Code.Br_S:i.OpCode=OpCodes.Br;break;case Code.Brfalse_S:i.OpCode=OpCodes.Brfalse;break;case Code.Brtrue_S:i.OpCode=OpCodes.Brtrue;break;case Code.Beq_S:i.OpCode=OpCodes.Beq;break;case Code.Bne_Un_S:i.OpCode=OpCodes.Bne_Un;break;case Code.Bge_S:i.OpCode=OpCodes.Bge;break;case Code.Bge_Un_S:i.OpCode=OpCodes.Bge_Un;break;case Code.Bgt_S:i.OpCode=OpCodes.Bgt;break;case Code.Bgt_Un_S:i.OpCode=OpCodes.Bgt_Un;break;case Code.Ble_S:i.OpCode=OpCodes.Ble;break;case Code.Ble_Un_S:i.OpCode=OpCodes.Ble_Un;break;case Code.Blt_S:i.OpCode=OpCodes.Blt;break;case Code.Blt_Un_S:i.OpCode=OpCodes.Blt_Un;break;case Code.Leave_S:i.OpCode=OpCodes.Leave;break;}}}
 static void Save(AssemblyDefinition a,string path){a.MainModule.Mvid=Guid.NewGuid();a.Write(path+".new");File.Delete(path);File.Move(path+".new",path);}
 public static void Main(string[] args){
  string dir=args[0];var resolver=new DefaultAssemblyResolver();resolver.AddSearchDirectory(dir);resolver.AddSearchDirectory(args[1]);var rp=new ReaderParameters{AssemblyResolver=resolver};
  var sdk=AssemblyDefinition.ReadAssembly(Path.Combine(dir,"RGDS.dll"),rp);
  var h=sdk.MainModule.Types.Single(t=>t.FullName=="RGDS.Handheld");
  var fna=AssemblyDefinition.ReadAssembly(Path.Combine(dir,"FNA.dll"),rp);var game=fna.MainModule.Types.Single(t=>t.FullName=="Microsoft.Xna.Framework.Game");
  var exit=game.Methods.Single(m=>m.Name=="Exit"&&m.Parameters.Count==0);var il=exit.Body.GetILProcessor();il.InsertBefore(exit.Body.Instructions[0],il.Create(OpCodes.Call,fna.MainModule.ImportReference(h.Methods.Single(m=>m.Name=="RequestExit"))));
  var tick=game.Methods.Single(m=>m.Name=="Tick");var ins=tick.Body.Instructions;
  var ti=tick.Body.GetILProcessor();var endDraw=ins.Single(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).Name=="EndDraw");ti.InsertAfter(endDraw,ti.Create(OpCodes.Call,fna.MainModule.ImportReference(h.Methods.Single(m=>m.Name=="DrawComplete"))));
  LongBranches(tick);Save(fna,Path.Combine(dir,"FNA.dll"));
  var app=AssemblyDefinition.ReadAssembly(Path.Combine(dir,"Game.exe"),rp);var finish=app.EntryPoint.Body.Instructions.Single(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).FullName=="System.Void System.Environment::Exit(System.Int32)");
  finish.Previous.OpCode=OpCodes.Nop;finish.Previous.Operand=null;finish.Operand=app.MainModule.ImportReference(h.Methods.Single(m=>m.Name=="FinishProcess"));Save(app,Path.Combine(dir,"Game.exe"));
  var engine=AssemblyDefinition.ReadAssembly(Path.Combine(dir,"ParisEngine.dll"),rp);var spawn=Method(engine,"Paris.Engine.Scene.GameObjectPoolManager","orig_SpawnObject");
  var log=spawn.Body.Instructions[0];var debug=spawn.Body.Instructions.First(i=>i.Operand is MethodReference&&((MethodReference)i.Operand).FullName=="System.Void NLog.Logger::Debug(System.String)");
  if(log.OpCode!=OpCodes.Ldsfld||!((FieldReference)log.Operand).FieldType.FullName.Equals("NLog.Logger"))throw new Exception("Unexpected pool debug block");
  var nlog=resolver.Resolve(new AssemblyNameReference("NLog",new Version(4,0,0,0)));var enabled=nlog.MainModule.Types.Single(t=>t.FullName=="NLog.Logger").Methods.Single(m=>m.Name=="get_IsDebugEnabled");var si=spawn.Body.GetILProcessor();
  si.InsertBefore(log,si.Create(OpCodes.Ldsfld,(FieldReference)log.Operand));si.InsertBefore(log,si.Create(OpCodes.Callvirt,engine.MainModule.ImportReference(enabled)));si.InsertBefore(log,si.Create(OpCodes.Brfalse,debug.Next));
  LongBranches(spawn);Save(engine,Path.Combine(dir,"ParisEngine.dll"));Console.WriteLine("Patched menu quit, post-disposal native exit, draw telemetry and lazy pool debug formatting.");
 }
}
