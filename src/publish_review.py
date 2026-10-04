"""Publish an already reviewed revision atomically; publication is not an iteration."""
from pathlib import Path
import argparse,json,shutil,os,datetime
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('revision',type=int);args=a.parse_args();r=args.revision
review=json.loads((root/'reviews'/f'review_r{r:02d}.json').read_text())
if not review.get('accepted'):raise SystemExit('This revision was not accepted in visual review.')
base='gpt6_astra_pro_mcp_blender_rgirljk'
required=[(f'{base}_r{r:02d}.blend',f'{base}.blend'),(f'{base}_r{r:02d}.glb',f'{base}.glb'),(f'{base}_web_r{r:02d}.glb',f'{base}_web.glb'),(f'{base}_lite_web_r{r:02d}.glb',f'{base}_lite_web.glb')]
for src,dest in required:
 if not (root/'build'/src).is_file():raise SystemExit('Missing export '+src)
for src,dest in required:
 target=root/'preview'/dest;temp=target.with_suffix(target.suffix+'.new');shutil.copyfile(root/'build'/src,temp);os.replace(temp,target)
s=json.loads((root/'preview/status.json').read_text());s.update(revision=r,score=review['score'],state='Reviewed checkpoint',notes=review['notes'],updated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),model=f'{base}_lite_web.glb',detailModel=f'{base}_web.glb',hero=f'front_r{r:02d}.png')
s['geometry']=json.loads((root/'build'/f'geometry_metrics_r{r:02d}.json').read_text())
s['renders']=[{'file':f'{v}_r{r:02d}.png','label':label} for v,label in [('face','Face and hair close-up'),('threequarter','Three-quarter inspection'),('back','Backpack and hands'),('side','Side silhouette')]]
s['downloads']=[{'file':f'{base}_lite_web.glb','label':'Lightweight web GLB · Meshopt'},{'file':f'{base}.glb','label':'Portable full-detail GLB'},{'file':f'{base}.blend','label':'Editable Blender scene'}]
if s.get('candidate',{}).get('revision')==r:s.pop('candidate',None)
temp=root/'preview/status.json.new';temp.write_text(json.dumps(s,indent=2));os.replace(temp,root/'preview/status.json')
review['publishedAt']=s['updated'];(root/'reviews'/f'review_r{r:02d}.json').write_text(json.dumps(review,indent=2))
print(f'PUBLISHED_REVISION {r}; completed review cycles remain {s["iterations"]}')
