#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <string.h>
#include <time.h>
static void*real_studio;static void*core;static void*master;static volatile uint32_t*state;static int state_checked;static float last=-1;
extern int FMOD_Studio_System_GetCoreSystem(void*,void**);
extern int FMOD_System_GetOutput(void*,int*);
extern int FMOD_System_SetOutput(void*,int);
extern int FMOD_System_SetDSPBufferSize(void*,unsigned,int);
extern int FMOD_System_GetMasterChannelGroup(void*,void**);
extern int FMOD_ChannelGroup_SetVolume(void*,float);
static void*real_function(const char*n){if(!real_studio)real_studio=dlopen("libfmodstudio.so.13",RTLD_NOW|RTLD_LOCAL);void*p=real_studio?dlsym(real_studio,n):NULL;if(!p){fprintf(stderr,"RGDS_AUDIO: missing native FMOD function %s: %s\n",n,dlerror());_exit(6);}return p;}
static void map_state(void){if(state_checked)return;state_checked=1;const char*p=getenv("RGDS_INPUT_STATE");if(!p)return;int fd=open(p,O_RDONLY);if(fd<0)return;void*m=mmap(NULL,4096,PROT_READ,MAP_SHARED,fd,0);close(fd);if(m!=MAP_FAILED)state=m;}
float mci_volume_gain(void){map_state();unsigned v=state?state[1]:2;if(v>10)v=10;float x=v/10.f;return .35f*x*x;}
static void mci_graphics_check(void);
static int forced_exit;
static int exit_requested(void){if(forced_exit)return 1;static int requested;const char*p=getenv("RGDS_EXIT_REQUEST");if(!requested&&p&&access(p,F_OK)==0)requested=1;return requested;}
static void frame_stats(void){
 static double first,last,sample,worst;static unsigned count;struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);double now=ts.tv_sec+ts.tv_nsec/1e9;
 if(!first){first=last=sample=now;const char*p=getenv("RGDS_SESSION_START");fprintf(stderr,"RGDS_FRAME: first game tick at session +%.3fs\n",p?now-atof(p):0);}
 double gap=now-last;last=now;if(gap>worst)worst=gap;count++;
 if(now-sample>=10){fprintf(stderr,"RGDS_FRAME: ticks/s=%.1f; worst gap=%.1fms\n",count/(now-sample),worst*1000);sample=now;count=0;worst=0;}
}
int mci_should_exit(void){frame_stats();mci_graphics_check();return exit_requested();}
void mci_audio_apply(void){if(!core)return;if(!master&&FMOD_System_GetMasterChannelGroup(core,&master))return;if(!master)return;float g=exit_requested()?0:mci_volume_gain();int rc=FMOD_ChannelGroup_SetVolume(master,g);if(!rc&&last!=g){fprintf(stderr,"RGDS_AUDIO: master gain %.5f\n",g);last=g;}}
int FMOD_Studio_System_Initialize(void*system,int channels,unsigned studioflags,unsigned flags,void*extra){
 static int(*real)(void*,int,unsigned,unsigned,void*);if(!real)real=real_function("FMOD_Studio_System_Initialize");
 core=NULL;master=NULL;int rc=FMOD_Studio_System_GetCoreSystem(system,&core);
 if(!rc&&core){int output=0;FMOD_System_GetOutput(core,&output);if(output==0){rc=FMOD_System_SetOutput(core,9);fprintf(stderr,"RGDS_AUDIO: native ALSA output selection=%d\n",rc);}FMOD_System_SetDSPBufferSize(core,1024,4);}
 rc=real(system,channels,studioflags,flags,extra);if(!rc){last=-1;mci_audio_apply();}else{core=NULL;master=NULL;}
 fprintf(stderr,"RGDS_AUDIO: studio initialization=%d\n",rc);return rc;
}
int FMOD_Studio_System_Update(void*system){static int(*real)(void*);if(!real)real=real_function("FMOD_Studio_System_Update");mci_audio_apply();int rc=real(system);mci_audio_apply();return rc;}
int FMOD_Studio_EventInstance_Start(void*event){static int(*real)(void*);if(!real)real=real_function("FMOD_Studio_EventInstance_Start");mci_audio_apply();return real(event);}
int FMOD_Studio_System_Release(void*system){static int(*real)(void*);if(!real)real=real_function("FMOD_Studio_System_Release");int rc=real(system);core=NULL;master=NULL;last=-1;return rc;}

/* Called by the existing game-thread exit hook. Never creates a GL context. */
static void mci_graphics_check(void){
 static void*sdl;static void*(*current)(void);static void*(*proc)(const char*);
 static int reported,errors;static unsigned frames;
 static const unsigned char*(*string)(unsigned);
 static unsigned(*error)(void);
 static void(*integer)(unsigned,int*);
 if(!sdl){sdl=dlopen("libSDL2-2.0.so.0",RTLD_NOW|RTLD_LOCAL);if(!sdl)return;current=dlsym(sdl,"SDL_GL_GetCurrentContext");proc=dlsym(sdl,"SDL_GL_GetProcAddress");}
 if(!current||!proc||!current())return;
 if(!string)string=proc("glGetString");
 if(!error)error=proc("glGetError");
 if(!integer)integer=proc("glGetIntegerv");
 if(!reported&&string&&integer){
  int limit=0;integer(0x0D33,&limit);
  const unsigned char*version=string(0x1F02);const unsigned char*extensions=string(0x1F03);
  fprintf(stderr,"RGDS_GL: ETC2 scenery profile; version=%s; max texture=%d; ASTC extension=%s\n",version?(const char*)version:"unknown",limit,extensions&&strstr((const char*)extensions,"texture_compression_astc")?"yes":"no");reported=1;
 }
 if(error&&errors<32&&(frames++%60)==0){unsigned code;while(errors<32&&(code=error())!=0){fprintf(stderr,"RGDS_GL: frame error 0x%04x\n",code);errors++;}}
}

/* Menu quit must reach the launcher even if the loop has already stopped. */
void mci_request_exit(void){
 if(forced_exit)return;forced_exit=1;
 const char*p=getenv("RGDS_EXIT_REQUEST");
 if(p){int fd=open(p,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(fd>=0){const char*msg="GAME_MENU_EXIT\n";write(fd,msg,strlen(msg));close(fd);}}
 mci_audio_apply();fprintf(stderr,"RGDS_EXIT: game quit notified launcher; audio muted\n");fflush(stderr);
}
/* Called only after the game's Run/Dispose/save cleanup has returned. */
void mci_finish_exit(void){fprintf(stderr,"RGDS_EXIT: disposal returned; ending native process\n");fflush(NULL);_exit(0);}
void mci_draw_complete(void){
 static double sample,last,worst;static unsigned count;struct timespec ts;
 clock_gettime(CLOCK_MONOTONIC,&ts);double now=ts.tv_sec+ts.tv_nsec/1e9;
 if(!sample){sample=last=now;}
 double gap=now-last;last=now;if(gap>worst)worst=gap;count++;
 if(now-sample>=10){fprintf(stderr,"RGDS_DRAW: presents/s=%.1f; worst gap=%.1fms\n",count/(now-sample),worst*1000);sample=now;count=0;worst=0;}
}
