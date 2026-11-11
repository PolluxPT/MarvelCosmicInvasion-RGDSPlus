#!/usr/bin/env python3
"""Standalone RGDS+ session launcher; no firmware or shared configuration edits."""
import os,sys,pathlib,subprocess,time,signal,struct,json,fcntl,traceback
from memory_safety import MemorySafety
from session_tools import stop_process,verify_runtime
ROOT=pathlib.Path(__file__).resolve().parent.parent
LOG=ROOT/'logs';LOG.mkdir(exist_ok=True)
lock=(LOG/'session.lock').open('w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('MARVEL Cosmic Invasion is already running.')
log=(LOG/'Launcher.log').open('w',buffering=1)
sys.stdout=log;sys.stderr=log
print('MARVEL Cosmic Invasion RGDS+ v1.0.0 Final',time.ctime(),flush=True)
started=time.monotonic()
def phase(message):print('[+%.3fs] %s'%(time.monotonic()-started,message),flush=True)
children=[];game=None;requested=None;saved=[];state=LOG/'input.bin';exitfile=LOG/'exit.request';exitfile.unlink(missing_ok=True)
perf=ROOT/'tools/performance-mode.py';governors=LOG/'governors.json'
def run(args,**kw):return subprocess.run([str(x) for x in args],**kw)
def request_exit(*args):
 if not exitfile.exists():exitfile.write_text('exit\n')
signal.signal(signal.SIGTERM,request_exit);signal.signal(signal.SIGINT,request_exit)
def change(path,value):
 p=pathlib.Path(path)
 try:
  old=p.read_text();saved.append((p,old));p.write_text(value+'\n');print('Session setting:',p,flush=True)
 except OSError as e:print('Session setting unavailable:',p,e,flush=True)
def remember(path):
 p=pathlib.Path(path)
 try:saved.append((p,p.read_text()))
 except OSError as e:print('Cannot save',p,e,flush=True)
def background(args,name,env=None):
 f=(LOG/name).open('w');p=subprocess.Popen([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT,env=env);children.append((p,f));return p
rc=1
memory_guard=MemorySafety(ROOT)
try:
 if os.uname().machine not in ('aarch64','arm64'):raise RuntimeError('This app requires the ARM64 RGDS+ Linux firmware.')
 for old in ['Game.log','Controls.log','Performance.log','MemoryTrace.txt']:
  (LOG/old).unlink(missing_ok=True)
 env=os.environ.copy()
 original_home=pathlib.Path(env.get('HOME','/root'))
 original_runtime=env.get('XDG_RUNTIME_DIR','')
 env['ALSA_PLUGIN_DIR']=str(ROOT/'runtime/alsa-plugins')
 if not env.get('PULSE_COOKIE'):
  for cookie in [original_home/'.config/pulse/cookie',original_home/'.pulse-cookie',pathlib.Path('/root/.config/pulse/cookie')]:
   if cookie.is_file():env['PULSE_COOKIE']=str(cookie);break
 if not env.get('PULSE_SERVER'):
  for socket in [pathlib.Path(original_runtime)/'pulse/native',pathlib.Path('/var/run/pulse/native'),pathlib.Path('/run/pulse/native'),pathlib.Path('/run/user/0/pulse/native')]:
   if socket.is_socket():env['PULSE_SERVER']='unix:'+str(socket);break
 for key in ['LD_PRELOAD','SDL_DYNAMIC_API','MONO_ENV_OPTIONS','MONO_AOT_MODE','MONO_AOT_CACHE','MONO_PATH','LD_LIBRARY_PATH']:
  env.pop(key,None)
 mono=ROOT/'runtime/mono';data=ROOT/'gamedata'
 native=[ROOT/'libs',mono/'lib',ROOT/'runtime/system-libs']
 env['LD_LIBRARY_PATH']=':'.join(map(str,native))+':/usr/lib:/lib'
 env['RGDS_SESSION_START']=str(started)
 env.update(SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',FNA_PLATFORM_BACKEND='SDL2',SDL_OPENGL_ES_DRIVER='1',SDL_VIDEO_WINDOW_POS='0,0',MONO_CFG_DIR=str(mono/'etc'),MONO_PATH=str(data)+':'+str(mono/'lib/mono/4.5'),MONO_IOMAP='all',MONO_GC_PARAMS='soft-heap-limit=192m,nursery-size=8m,major=marksweep-conc',MONO_LOG_LEVEL='warning',FNA3D_FORCE_DRIVER='OpenGL',FNA3D_OPENGL_FORCE_ES3='1',SDL_VIDEODRIVER='wayland',SDL_VIDEO_FULLSCREEN_DISPLAY='0',SDL2_SWAP_LCD='0',SDL_AUDIODRIVER='dummy',FMOD_ALSA_DEVICE='default',RGDS_INPUT_STATE=str(state),RGDS_EXIT_REQUEST=str(exitfile))
 # FAudio is only used by the skipped video; FMOD opens ALSA independently.
 # Keeping that unused SDL audio device dummy avoids two exclusive ALSA clients.
 for conf in ['/usr/share/alsa/alsa.conf','/etc/alsa/alsa.conf']:
  if pathlib.Path(conf).exists():
   env['ALSA_CONFIG_PATH']=conf+':'+str(ROOT/'tools/asound-mci.conf');env['FMOD_ALSA_DEVICE']='mci_default';break
 display=env.get('WAYLAND_DISPLAY','wayland-0');runtime=env.get('XDG_RUNTIME_DIR','')
 if not runtime or not (pathlib.Path(runtime)/display).exists():
  for d in [f'/run/user/{os.getuid()}','/run/user/0','/run','/var/run']:
   if (pathlib.Path(d)/display).exists():runtime=d;break
 if not runtime or not (pathlib.Path(runtime)/display).exists():raise RuntimeError('The stock Wayland display socket was not found.')
 env.update(XDG_RUNTIME_DIR=runtime,WAYLAND_DISPLAY=display)
 phase('Loading measured RGDS+ controller profile')
 run([sys.executable,ROOT/'tools/controller_profile.py',ROOT],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=10)
 profile=json.loads((LOG/'ControllerProfile.json').read_text());mapping=profile['mapping'];env['SDL_GAMECONTROLLERCONFIG']=mapping
 home=ROOT/'savedata/home';config=ROOT/'savedata/config';share=home/'.local/share'
 for p in [home,config,share]:p.mkdir(parents=True,exist_ok=True)
 env.update(HOME=str(home),XDG_CONFIG_HOME=str(config),XDG_DATA_HOME=str(share))
 executable=mono/'bin/mono-sgen';executable.chmod(executable.stat().st_mode|0o111)
 print('Audio plug-ins:',env['ALSA_PLUGIN_DIR'],'Pulse server:',env.get('PULSE_SERVER','automatic'),flush=True)
 print('Display:',runtime,display,'SDL controller:',mapping,flush=True)
 phase('Checking runtime')
 verify_runtime(ROOT,env,log)
 phase('Checking sound output')
 with (LOG/'AudioProbe.log').open('w') as audio_log:
  result=run([sys.executable,ROOT/'tools/audio_setup.py',ROOT],env=env,stdout=audio_log,stderr=subprocess.STDOUT,timeout=25)
 if result.returncode==0:
  audio=json.loads((LOG/'AudioSelection.json').read_text())
  if audio.get('config'):env['ALSA_CONFIG_PATH']=audio['config']
  print('Audio route:',audio['route'],flush=True)
 else:print('Audio preflight failed; retaining system default for FMOD.',flush=True)
 phase('Preparing memory safety')
 memory_guard.prepare()
 if exitfile.exists():raise InterruptedError('Exit requested during startup.')
 state.write_bytes(struct.pack('<II',0,2)+bytes(4088))
 remember('/sys/class/anbernic_misc/openbor_volume')
 change('/sys/class/backlight/backlight/brightness','0');change('/sys/class/backlight/backlight/bl_power','4')
 run([sys.executable,perf,'apply',governors],stdout=log,stderr=subprocess.STDOUT)
 daemon=background([sys.executable,ROOT/'tools/device.py',state,exitfile],'Controls.log')
 time.sleep(.15)
 if daemon.poll() is not None:raise RuntimeError('The physical button service did not find the RGDS+ input devices.')
 (LOG/'MemoryStart.txt').write_text(pathlib.Path('/proc/meminfo').read_text())
 phase('Starting game: precompiled ARM64 assemblies enabled')
 gamefile=(LOG/'Game.log').open('w');game=subprocess.Popen([str(executable),'--config',str(mono/'etc/mono/config'),'-O=all','Game.exe','-forcedraw'],cwd=data,env=env,stdout=gamefile,stderr=subprocess.STDOUT,start_new_session=True)
 background([sys.executable,perf,'watch',game.pid],'Performance.log')
 while game.poll() is None:
  if memory_guard.poll() and not exitfile.exists():
   print('Critical memory pressure; requesting normal game exit.',flush=True);request_exit()
  if daemon.poll() is not None:request_exit();print('Button service stopped; requesting game exit',flush=True)
  if exitfile.exists():
   if requested is None:
    requested=time.monotonic();phase('Exit requested: allowing game disposal')
   elif time.monotonic()-requested>2:
    phase('Game did not finish disposal; stopping its process')
    stop_process(game,.75)
    break
  time.sleep(.1)
 rc=game.wait();gamefile.close();phase('Game process stopped: '+str(rc))
 reason='normal return' if rc==0 else ('requested stop after disposal timeout' if requested is not None else 'unexpected game termination')
 (LOG/'SessionResult.json').write_text(json.dumps({'reason':reason,'exit_code':rc,'elapsed_seconds':round(time.monotonic()-started,3)},indent=2)+'\n')
except Exception:traceback.print_exc(file=log)
finally:
 if game and game.poll() is None:stop_process(game,.75)
 phase('Restoring handheld session')
 for p,f in children:
  if p.poll() is None:
   p.terminate()
   try:p.wait(timeout=.5)
   except subprocess.TimeoutExpired:p.kill();p.wait()
  f.close()
 try:memory_guard.close()
 except Exception:traceback.print_exc(file=log)
 if governors.exists():run([sys.executable,perf,'restore',governors],stdout=log,stderr=subprocess.STDOUT)
 for p,v in reversed(saved):
  try:p.write_text(v);print('Restored:',p,flush=True)
  except OSError as e:print('Restore failed:',p,e,flush=True)
 try:(LOG/'MemoryEnd.txt').write_text(pathlib.Path('/proc/meminfo').read_text())
 except OSError:pass
 crash=ROOT/'gamedata/mci_crash.txt'
 if crash.exists():
  try:(LOG/'Crash.txt').write_bytes(crash.read_bytes());crash.unlink()
  except OSError:pass
 phase('Returning to handheld menu');print('Finished:',time.ctime(),flush=True);log.flush()

raise SystemExit(0 if rc==0 or requested is not None else 1)
