"""Poppler page rendering and contact sheets for visual QA, not a deliverable."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
RENDER=ROOT/'tmp/pdfs/prepared_20260910/render'
RENDER.mkdir(parents=True,exist_ok=True)
for pdf in sorted((ROOT/'output/pdf/prepared_20260910').glob('*.pdf')):
    folder=RENDER/pdf.stem
    folder.mkdir(exist_ok=True)
    subprocess.run(['pdftoppm','-r','85','-png',str(pdf),str(folder/'page')],check=True,capture_output=True)
    pages=sorted(folder.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
    for batch in range(0,len(pages),6):
        sheet=Image.new('RGB',(1400,2860),'#d8dce2')
        draw=ImageDraw.Draw(sheet)
        for i,path in enumerate(pages[batch:batch+6]):
            im=Image.open(path).convert('RGB')
            im.thumbnail((680,910))
            x=(i%2)*700+10
            y=(i//2)*950+25
            sheet.paste(im,(x,y))
            draw.text((x,y-18),f'{pdf.stem} page {batch+i+1}',fill='black')
        dest=folder/f'contact-{batch//6+1}.png'
        sheet.save(dest)
        print(dest,flush=True)
