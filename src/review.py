"""Record a completed build/preview/visual-review cycle, never synthetic iterations."""
import json,sys,datetime,pathlib,shutil,os
p=pathlib.Path(__file__).resolve().parents[1];s=json.loads((p/'preview/status.json').read_text());r=int(sys.argv[1]);score=int(sys.argv[2]);note=sys.argv[3]
for ext in ['glb','blend']:
    src=p/'build'/f'gpt6_astra_pro_mcp_blender_rgirljk_r{r:02d}.{ext}'
    if src.exists():
        dest=p/'preview'/f'gpt6_astra_pro_mcp_blender_rgirljk.{ext}';tmp=dest.with_suffix(dest.suffix+'.new');shutil.copyfile(src,tmp);os.replace(tmp,dest)
s.update(revision=r,score=score,iterations=s.get('iterations',0)+1,state='Reviewed - improving',notes=note,updated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),model='gpt6_astra_pro_mcp_blender_rgirljk.glb',hero=f'front_r{r:02d}.png')
websrc=p/'build'/f'gpt6_astra_pro_mcp_blender_rgirljk_web_r{r:02d}.glb'
if websrc.exists():
    dest=p/'preview'/'gpt6_astra_pro_mcp_blender_rgirljk_web.glb';tmp=dest.with_suffix('.glb.new');shutil.copyfile(websrc,tmp);os.replace(tmp,dest);s['model']=dest.name
s['renders']=[{'file':f'{v}_r{r:02d}.png','label':label} for v,label in [('face','Face and hair close-up'),('threequarter','Three-quarter inspection'),('back','Backpack and hidden hands'),('side','Side silhouette')] if (p/'preview'/f'{v}_r{r:02d}.png').exists()]
s['downloads']=[{'file':'gpt6_astra_pro_mcp_blender_rgirljk.glb','label':'Portable 3D model - GLB'},{'file':'gpt6_astra_pro_mcp_blender_rgirljk.blend','label':'Editable Blender scene'}]
s.setdefault('history',[]).append(f'Iteration {s["iterations"]} / revision {r}: {score}/100 - {note}')
(p/'preview/status.json').write_text(json.dumps(s,indent=2));(p/'build'/f'review_r{r:02d}.json').write_text(json.dumps(s,indent=2));print(f'Review recorded: actual iteration {s["iterations"]}; subjective score {score}/100')
