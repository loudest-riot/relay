#!/usr/bin/env python3
"""Seamlessly looping Spotify Canvas for nøfuture: Slight Chance of Misery.
Source: official artist-owned release cover and Hines imagery in repo /assets.
"""
from pathlib import Path
import math, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"assets"
OUT=ROOT/"canvas"/"export"/"slight-chance-of-misery-canvas.mp4"
OUT.parent.mkdir(parents=True,exist_ok=True)
W,H,FPS,N=720,1280,24,168

def crop(path,fx=.5):
    im=Image.open(path).convert("RGB")
    iw,ih=im.size
    h=round(H*1.10)
    w=math.ceil(iw*h/ih)
    if w<W:
        w=round(W*1.10)
        h=math.ceil(ih*w/iw)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    left=round(max(0,w-W)*fx)
    top=max(0,(h-H)//2)
    return np.asarray(im.crop((left,top,left+W,top+H)),dtype=np.float32)

def main():
    forest=crop(A/"hines-002.jpg",.72)
    forest *= np.array([.84,.74,1.02])[None,None,:]
    starfield=crop(A/"crossed-by-stars.jpg",.95)
    starfield *= np.array([.80,.83,1.10])[None,None,:]
    yy,xx=np.mgrid[0:H,0:W]
    glow=np.exp(-(((xx-W*.50)/(W*.58))**2+((yy-H*.40)/(H*.26))**2)*2)
    forest[:,:,0]+=glow*22
    forest[:,:,1]+=glow*4
    forest[:,:,2]+=glow*17
    cover=Image.open(A/"misery.jpg").convert("RGB").resize((638,638),Image.Resampling.LANCZOS)
    cov=np.asarray(cover,dtype=np.float32)
    cy,cx=np.mgrid[0:638,0:638]
    nx=(cx-319)/319
    ny=(cy-319)/319
    soft=np.clip((1-(nx**4+ny**4)**.75)*1.65,0,1)
    soft=np.asarray(Image.fromarray(np.uint8(soft*255)).filter(ImageFilter.GaussianBlur(18)),dtype=np.float32)/255
    edge=np.clip(1-.35*((xx-W*.5)**2/(W*.9)**2+(yy-H*.52)**2/(H*.8)**2),.63,1)
    rng=np.random.default_rng(27843)
    sparks=[(int(rng.integers(20,W-20)),int(rng.integers(30,530)),float(rng.uniform(.5,1.9)),float(rng.random()*2*math.pi)) for i in range(32)]
    proc=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)],stdin=subprocess.PIPE)
    for f in range(N):
        t=2*math.pi*f/N
        frame=np.roll(forest,(round(6*math.cos(t)),round(7*math.sin(t))),axis=(0,1)).copy()
        blend=.13+.08*(.5+.5*math.cos(t-.65))
        frame=frame*(1-blend)+np.maximum(frame,starfield*.76)*blend
        for y in range(round(H*.59),H):
            shift=round((y/H-.59)*18*math.sin(t+y*.042))
            frame[y]=np.roll(frame[y],shift,axis=0)
        op=.42+.46*(.5-.5*math.cos(t))
        x=(W-638)//2+round(5*math.sin(t))
        y=350+round(7*math.sin(t+.4))
        a=soft[:,:,None]*op
        frame[y:y+638,x:x+638] = frame[y:y+638,x:x+638]*(1-a)+cov*a
        im=Image.fromarray(np.uint8(np.clip(frame,0,255)))
        d=ImageDraw.Draw(im,"RGBA")
        for sx,sy,r,phase in sparks:
            tw=.5+.5*math.cos(t+phase)
            d.ellipse((sx-r,sy-r,sx+r,sy+r),fill=(220,234,255,round(85*tw)))
        frame=np.asarray(im,dtype=np.float32)*edge[:,:,None]
        grain=(np.sin(xx*.337+yy*.573)+np.cos(xx*.983-yy*.221))*1.15
        frame+=grain[:,:,None]
        proc.stdin.write(np.uint8(np.clip(frame,0,255)).tobytes())
    proc.stdin.close()
    if proc.wait(): raise RuntimeError("Canvas ffmpeg encode failed")
    print("EXPORT",OUT,OUT.stat().st_size,"bytes",N/FPS,"seconds")

if __name__=="__main__":
    main()
