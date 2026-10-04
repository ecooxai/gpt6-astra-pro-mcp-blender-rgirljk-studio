"""Record a visually inspected build separately from model publication."""
from pathlib import Path
import argparse,json,os,datetime,subprocess
from PIL import Image
root=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('revision',type=int);a.add_argument('score',type=int);a.add_argument('notes');a.add_argument('--accepted',action='store_true');args=a.parse_args()
if not 0<=args.score<=100:raise SystemExit('Score must be 0..100.')
views=['front','face','threequarter','back','side'];files=[root/'preview'/f'{v}_r{args.revision:02d}.png' for v in views]
if not all(f.is_file() for f in files):raise SystemExit('A five-view build is required before recording its visual review.')
journal=root/'reviews'/f'review_r{args.revision:02d}.json'
if journal.exists():raise SystemExit('This revision is already reviewed; do not count a rerender twice.')
evidence=root/'reviews/renders'/f'r{args.revision:02d}';evidence.mkdir(parents=True,exist_ok=True)
for view,file in zip(views,files):
 im=Image.open(file).convert('RGB');im.thumbnail((1000,1000));im.save(evidence/(view+'.jpg'),quality=90,optimize=True)
s=json.loads((root/'preview/status.json').read_text());iteration=s.get('iterations',0)+1
entry={'revision':args.revision,'iteration':iteration,'score':args.score,'accepted':args.accepted,'notes':args.notes,'reviewBasis':'Direct visual inspection of five rendered views; subjective resemblance score, not a computed similarity metric.','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'evidence':[str((evidence/(v+'.jpg')).relative_to(root)) for v in views]}
journal.parent.mkdir(exist_ok=True);journal.write_text(json.dumps(entry,indent=2))
s['iterations']=iteration;s['candidate']={'revision':args.revision,'score':args.score,'accepted':args.accepted,'notes':args.notes,'files':[f.name for f in files]};s['updated']=entry['recordedAt'];s['state']='Reviewed candidate; export pending' if args.accepted else 'Refining candidate'
s.setdefault('history',[]).append(f'Iteration {iteration} / revision {args.revision}: {args.score}/100 — {args.notes}')
temp=root/'preview/status.json.new';temp.write_text(json.dumps(s,indent=2));os.replace(temp,root/'preview/status.json')
print(json.dumps(entry,indent=2))
