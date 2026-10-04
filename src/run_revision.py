"""Render from an immutable copy of authored model source; never count a review here."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,datetime
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser(add_help=False);a.add_argument('--revision',type=int,required=True);a.add_argument('--reuse-snapshot',action='store_true');args,rest=a.parse_known_args()
snapshot=root/'build/jobs'/f'r{args.revision:03d}'/'source'
if snapshot.exists() and not args.reuse_snapshot:raise SystemExit('Snapshot exists. Use --reuse-snapshot for an exact rerender, or a new revision for changed geometry.')
if not snapshot.exists():
 snapshot.mkdir(parents=True)
 for src in (root/'src').glob('*.py'):shutil.copy2(src,snapshot/src.name)
 manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in snapshot.glob('*.py')}
 (snapshot.parent/'source_manifest.json').write_text(json.dumps({'revision':args.revision,'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':manifest},indent=2))
blender=Path(os.environ.get('BLENDER_BIN','/home/dev/.local/opt/blender-4.2.3-linux-x64/blender'))
if not blender.is_file():raise SystemExit('Set BLENDER_BIN to a working Blender 4.2+ executable.')
env=os.environ.copy();env['RGIRL_PROJECT_ROOT']=str(root)
cmd=[str(blender),'-b','-t',env.get('BLENDER_THREADS','6'),'--factory-startup','--python',str(snapshot/'build_character.py'),'--','--revision',str(args.revision),*rest]
print('IMMUTABLE_SOURCE',snapshot,flush=True)
result=subprocess.run(cmd,cwd=root,env=env)
raise SystemExit(result.returncode)
