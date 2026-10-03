"""Publish only reviewed assets; reference remains an external comparison image."""
from pathlib import Path
import shutil,json,subprocess
root=Path(__file__).resolve().parents[1];dest=root/'build/github-pages';dest.mkdir(parents=True,exist_ok=True)
s=json.loads((root/'preview/status.json').read_text())
files=['index.html','viewer.js','status.json',s['model'],s['hero']]+[x['file'] for x in s['renders']]+[x['file'] for x in s.get('downloads',[])]
for old in dest.iterdir():
    if old.name!='.git':
        if old.is_dir():shutil.rmtree(old)
        else:old.unlink()
for name in set(files):
    src=root/'preview'/name
    if src.exists():shutil.copy2(src,dest/name)
p=dest/'index.html';p.write_text(p.read_text().replace('src="reference.png"','src="https://lesswebdisk.my-team-8435.chatgpt.site/raw/u-oKDfM5n2PVKJ/3d/rgirljk/rgirljk.png"'))
(dest/'.nojekyll').touch()
def git(*args):subprocess.run(['git',*args],cwd=dest,check=True)
if not (dest/'.git').exists():
    git('init','-b','gh-pages');git('remote','add','origin','https://github.com/ecooxai/gpt6-astra-pro-mcp-blender-rgirljk-studio.git')
git('config','user.name','GPT-6 Astra Pro');git('config','user.email','agent@local');git('add','-A')
if subprocess.run(['git','diff','--cached','--quiet'],cwd=dest).returncode:
    git('commit','-m',f'Publish visually reviewed original character revision {s["revision"]}')
git('push','-u','origin','gh-pages')
print('PAGES_ASSETS_PUSHED',s['revision'])
