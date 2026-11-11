from pathlib import Path
import ast,json,hashlib,zipfile
root=Path(__file__).resolve().parent.parent
bad={'.exe','.dll','.so','.xnb','.bank','.ogv','.png','.jpg','.jpeg','.mp4'}
for p in root.rglob('*'):
 if not p.is_file() or '.git' in p.parts:continue
 assert p.suffix.lower() not in bad,p
 assert not any(x.lower() in ('gamedata','savedata','logs') for x in p.relative_to(root).parts),p
 assert 'PERSONAL' not in p.name and 'TestLogs' not in p.name,p
 if p.suffix=='.zip':
  assert p.name=='MARVELCosmicInvasion_RGDSPlus_v1.0.0_Final_Update.zip',p
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   assert all(Path(n).suffix.lower() not in bad for n in z.namelist())
launcher=root/'release/APPS/MarvelCosmicInvasion_RGDSPlus/tools/launcher.py'
code=launcher.read_text();ast.parse(code)
assert 'zipfile' not in code and 'TestLogs.zip' not in code
profile=json.loads((launcher.parent.parent/'runtime/session-profile.json').read_text())
item=next(x for x in profile['files'] if x['path']=='tools/launcher.py')
assert item['sha256']==hashlib.sha256(launcher.read_bytes()).hexdigest()
assert item['size']==launcher.stat().st_size
print('PASS: no commercial payload or private files; launcher syntax/profile; no automatic ZIP export.')
