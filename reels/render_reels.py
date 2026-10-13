#!/usr/bin/env python3
"""Render two silent portrait promo reels using official Loudest Riot artwork."""
import math
import subprocess
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT = ROOT / "reels" / "exports"
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1080, 1920, 24
DARK = (3, 11, 26)
BLUE = (142, 193, 255)
WHITE = (245, 247, 246)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

@lru_cache(maxsize=16)
def artwork(file):
    return Image.open(ASSETS / file).convert("RGB")

@lru_cache(maxsize=16)
def background(file):
    art = artwork(file)
    bg = ImageOps.fit(art, (1300, 2180), method=Image.Resampling.LANCZOS, centering=(.5, .56))
    bg = bg.filter(ImageFilter.GaussianBlur(39))
    bg = ImageEnhance.Color(bg).enhance(1.38)
    return Image.blend(bg, Image.new("RGB", bg.size, DARK), .45)

@lru_cache(maxsize=15)
def cover(file):
    return ImageOps.fit(artwork(file), (735, 735), method=Image.Resampling.LANCZOS)

@lru_cache(maxsize=10)
def font(size, bold=False, mono=False):
    return ImageFont.truetype(MONO if mono else BOLD, size)

@lru_cache(maxsize=1)
def logo():
    im = Image.open(ASSETS / "brand" / "nofuture-waveform-white.png").convert("RGBA")
    im = im.crop(im.getbbox())
    im.thumbnail((540,230),Image.Resampling.LANCZOS)
    return im

@lru_cache(maxsize=1)
def wash_layer():
    wash = Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(wash)
    for y in range(H):
        top=max(0,1-y/510)
        bot=max(0,(y-1210)/710)
        alpha=int(min(207,85+100*top+100*bot))
        d.line((0,y,W,y),fill=(3,8,22,alpha),width=1)
    return wash

def gradient(im):
    return Image.alpha_composite(im.convert("RGBA"),wash_layer())

def centered(draw,y,txt,size,color=WHITE,mono=False):
    ft=font(size,not mono,mono)
    x=(W-draw.textbbox((0,0),txt,font=ft)[2])/2
    draw.text((x,y),txt,font=ft,fill=color)

def make_shot(file,t,dur,index,total,title,subtitle,dark=False):
    frac=min(1,max(0,t/dur))
    bg=background(file)
    bx=int(70+68*math.sin(2*math.pi*frac+.4))
    by=int(115+60*math.cos(frac*2.5))
    frame=bg.crop((bx,by,bx+W,by+H)).convert("RGBA")
    overlay=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(overlay)
    d.rectangle((0,0,W,H),fill=(3,7,20,104 if dark else 61))
    d.line((77,290,1003,290),fill=(*BLUE,130),width=2)
    d.line((77,1542,1003,1542),fill=(*BLUE,100),width=2)
    d.line((77,296,77,353),fill=(*BLUE,160),width=3)
    d.ellipse((966,321,977,332),fill=(255,156,108,240))
    for x,y in [(895,190),(190,467),(919,1450),(139,1368)]:
        if index%2==0:
            d.ellipse((x-2,y-2,x+2,y+2),fill=(161,202,254,190))
    frame=Image.alpha_composite(frame,overlay)
    base=cover(file)
    s=int(735*(1.02+.037*frac))
    c=base.resize((s,s),Image.Resampling.BICUBIC).convert("RGBA")
    x=(W-s)//2+int(10*math.sin(frac*2.5))
    y=610-int(15*frac)
    shadow=Image.new("RGBA",(s+40,s+40),(0,0,0,0))
    ImageDraw.Draw(shadow).rectangle((20,20,s+20,s+20),fill=(0,0,0,160))
    shadow=shadow.filter(ImageFilter.GaussianBlur(20))
    frame.alpha_composite(shadow,(x-20,y-20))
    alpha=min(1,frac/.16,(1-frac)/.14)
    c.putalpha(int(255*max(0,alpha)))
    frame.alpha_composite(c,(x,y))
    frame=gradient(frame)
    d=ImageDraw.Draw(frame)
    d.text((79,182),"LOUDEST RIOT SOUNDS",font=font(24,mono=True),fill=(221,234,255,235))
    d.text((79,340),"HINES PARK / TRANSMISSIONS",font=font(25,mono=True),fill=BLUE)
    if title:
        centered(d,1365,title,48 if len(title)<25 else 41)
    if subtitle:
        centered(d,1433,subtitle,22,BLUE,True)
    d.text((79,1592),f"{index:02d}  /  {total:02d}",font=font(32,mono=True),fill=(230,239,255))
    d.rectangle((77,1664,1003,1667),fill=(72,111,166))
    d.rectangle((77,1664,77+int(926*(index-1+frac)/total),1667),fill=BLUE)
    return frame.convert("RGB")

def finale(file,t,dur,top,message,small):
    bg=background(file)
    frac=min(1,max(0,t/dur))
    bx=int(100+45*frac); by=int(100+35*frac)
    fr=bg.crop((bx,by,bx+W,by+H)).convert("RGBA")
    fr=Image.blend(fr,Image.new("RGBA",(W,H),(1,8,23,255)),.50)
    fr=gradient(fr)
    d=ImageDraw.Draw(fr)
    d.line((115,320,965,320),fill=(98,176,255,210),width=3)
    d.text((117,359),top,font=font(31,mono=True),fill=BLUE)
    centered(d,648,message,58)
    centered(d,735,small,34,BLUE,True)
    l=logo()
    fr.alpha_composite(l,((W-l.width)//2,925))
    d=ImageDraw.Draw(fr)
    centered(d,1280,"RELAY.LOUDESTRIOT.COM",31,WHITE,True)
    centered(d,1382,"LOUDEST RIOT SOUNDS",24,BLUE,True)
    return fr.convert("RGB")

def render(filename,shots,ending,segtime,endtime):
    outfile=OUT/filename
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-vcodec","rawvideo",
         "-s",f"{W}x{H}","-pix_fmt","rgb24","-r",str(FPS),"-i","-","-an",
         "-vcodec","libx264","-pix_fmt","yuv420p","-preset","veryfast","-crf","20",
         "-movflags","+faststart","-r",str(FPS),str(outfile)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        total=len(shots)
        for idx,(file,title,subtitle) in enumerate(shots,1):
            for j in range(round(FPS*segtime)):
                im=make_shot(file,j/FPS,segtime,idx,total,title,subtitle,dark=filename.startswith("02"))
                proc.stdin.write(im.tobytes())
        for j in range(round(FPS*endtime)):
            im=finale(ending[0],j/FPS,endtime,*ending[1:])
            proc.stdin.write(im.tobytes())
    except BrokenPipeError:
        raise RuntimeError("ffmpeg terminated early")
    finally:
        try:proc.stdin.close()
        except Exception:pass
    if proc.wait()!=0:
        raise RuntimeError("ffmpeg failed: "+str(proc.returncode))
    print(f"Created {outfile}, {outfile.stat().st_size:,} bytes",flush=True)

if __name__=="__main__":
    render("01-seven-transmissions.mp4",[
        ("hines-002.jpg","ONE LANDSCAPE","DUSK / WATER"),
        ("crossed-by-stars.jpg","UNDER THE STARS","LIGHT / DISTANCE"),
        ("hines-001.jpg","THROUGH THE WOODS","TRAIL / MOTION"),
        ("middle-rouge.jpg","FOLLOW THE SIGNAL","ROADS / RIVERS"),
        ("misery.jpg","THROUGH THE WEATHER","STORM / STATIC"),
        ("dead-stars.jpg","INTO THE DARK","ORBIT / MEMORY"),
        ("hines-002.jpg","BACK TO THE FIELD","REFLECTION / RETURN")
    ],("hines-002.jpg","A CYCLE OF SOUND","SEVEN COMPOSITIONS","ONE LANDSCAPE"),2.0,3.0)
    render("02-darker-signal.mp4",[
        ("misery.jpg","THE WEATHER TURNS","SLIGHT CHANCE OF MISERY"),
        ("crossed-by-stars.jpg","THE STARS REMAIN","CROSSED BY STARS"),
        ("hines-001.jpg","THE SIGNAL CONTINUES","THROUGH THE WOODS"),
        ("hines-002.jpg","THE LANDSCAPE MOVES","FOUR SPOTIFY CANVASES LIVE")
    ],("misery.jpg","THE DARKER SIGNAL","SEVEN COMPOSITIONS","ONE COLLECTION"),3.0,3.0)
