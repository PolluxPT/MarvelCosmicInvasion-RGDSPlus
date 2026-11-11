using System;
using System.Runtime.InteropServices;
using Microsoft.Xna.Framework;
namespace RGDS {
 public static class Handheld {
  [DllImport("libmci_audio.so",CallingConvention=CallingConvention.Cdecl)] static extern int mci_should_exit();
  [DllImport("libmci_audio.so",CallingConvention=CallingConvention.Cdecl)] static extern void mci_request_exit();
  [DllImport("libmci_audio.so",CallingConvention=CallingConvention.Cdecl)] static extern void mci_finish_exit();
  [DllImport("libmci_audio.so",CallingConvention=CallingConvention.Cdecl)] static extern void mci_draw_complete();
  static bool exiting;
  public static void Frame(Game game) {
   if(!exiting&&mci_should_exit()!=0){exiting=true;Console.WriteLine("RGDS_INPUT: exit requested; stopping game loop");game.Exit();}
  }
  public static void RequestExit(){mci_request_exit();}
  public static void FinishProcess(){Console.Out.Flush();Console.Error.Flush();mci_finish_exit();}
  public static void DrawComplete(){mci_draw_complete();}

 }
}
