from pathlib import Path
from PIL import Image,ImageDraw
import sys
r=int(sys.argv[1]);root=Path(__file__).resolve().parents[1];p=root/'preview';names=['front','threequarter','back','side'];sheet=Image.new('RGB',(1440,1650),(22,26,32));d=ImageDraw.Draw(sheet)
for i,name in enumerate(names):
    im=Image.open(p/f'{name}_r{r:02d}.png').convert('RGB');im.thumbnail((720,810));x=(i%2)*720+(720-im.width)//2;y=(i//2)*825;sheet.paste(im,(x,y));d.text(((i%2)*720+16,y+810),f'Revision {r} / {name}',fill=(230,230,230))
out=p/f'inspection_r{r:02d}.jpg';sheet.save(out,quality=91);print(out)
