#!/usr/bin/env python3
"""Slight Chance of Misery: seamless, silent, text-free Spotify Canvas.

Source: only official nøfuture cover artwork from this repository.
NO title, artist name, album-cover lettering, UI overlays, or logos in ANY frame.
Only use verified title-free rectangular crops of each printed cover.
"""
from pathlib import Path
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "canvas" / "export" / "slight-chance-of-misery-canvas.mp4"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
W,H,FPS,FRAMES = 720,1280,24,168

# The text on the 512px release covers is entirely OUTSIDE these crop boxes.
# Hines: crop below the top-left title block.
# Crossed: crop right of all the release typography.
# Misery: only use right-hand storm/treeline, beyond the title's rightmost letter.
SAFE_CROPS = {
    "hines-002.jpg": (232,145,508,508),
    "crossed-by-stars.jpg": (352,16,509,501),
    "misery.jpg": (397,111,509,508),
}

def safe_image(name, focus_x=0.5):
    image=Image.open(ASSETS/name).convert("RGB")
    box=SAFE_CROPS[name]
    sx,sy=image.size
    image=image.crop(tuple(int(v * scale / 512) for v,scale in zip(box,(sx,sy,sx,sy))))
    iw,ih=image.size
    factor=max(W/iw,H/ih)*1.04
    image=image.resize((math.ceil(iw*factor),math.ceil(ih*factor)),Image.Resampling.LANCZOS)
    nw,nh=image.size
    x=round((nw-W)*focus_x)
    y=(nh-H)//2
    return np.asarray(image.crop((x,y,x+W,y+H)),dtype=np.float32)

def main():
    forest=safe_image("hines-002.jpg",.43)
    stars=safe_image("crossed-by-stars.jpg",.53)
    storm=safe_image("misery.jpg",.49)
    y,x=np.mgrid[:H,:W]
    # Keep the real sunset glints and water, but darken to match the release.
    forest *= np.array([.88,.78,1.03],dtype=np.float32)[None,None,:]
    stars *= np.array([.78,.83,1.03],dtype=np.float32)[None,None,:]
    storm *= np.array([.91,.90,1.07],dtype=np.float32)[None,None,:]
    # Atmospheric cloud from actual official Misery artwork.
    cloud_mask=(np.exp(-((x-W*.69)/(W*.60))**2-((y-H*.29)/(H*.35))**2)*.38)[:,:,None]
    # Stars are brightest near upper sky, not a full-frame cover fade.
    stars_mask=(np.clip(1-y/(H*.81),0,1)*.32)[:,:,None]
    scene=forest*(1-cloud_mask)+storm*cloud_mask
    scene=scene*(1-stars_mask)+np.maximum(scene,stars)*stars_mask
    # Sunset glow keeps dark imagery from getting dull.
    glow=np.exp(-((x-W*.42)/(W*.52))**2-((y-H*.51)/(H*.20))**2)
    scene[:,:,0]+=glow*24
    scene[:,:,1]+=glow*4
    scene[:,:,2]+=glow*12
    # Vignette and retained midtone brightness.
    v=1-.23*((x-W*.5)/(W*.77))**2-.21*((y-H*.46)/(H*.83))**2
    scene*=np.clip(v,.69,1)[:,:,None]
    rng=np.random.default_rng(97412)
    specks=[(int(rng.integers(20,W-20)),int(rng.integers(36,550)),float(rng.uniform(.55,1.8)),float(rng.uniform(0,2*math.pi))) for _ in range(31)]
    grain=(np.sin(x*.337+y*.573)+np.cos(x*.983-y*.221))*1.14
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(OUTPUT)]
    encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(FRAMES):
        phase=2*math.pi*n/FRAMES
        # All motion is periodic to create a clean loop.
        dy=int(round(4*math.cos(phase)))
        dx=int(round(6*math.sin(phase)))
        frame=np.roll(scene,(dy,dx),(0,1)).copy()
        # Soft, periodic wave drift only in reflected water.
        for row in range(int(H*.58),H):
            shift=round((row/H-.58)*16*math.sin(phase+row*.047))
            frame[row]=np.roll(frame[row],shift,axis=0)
        img=Image.fromarray(np.uint8(np.clip(frame,0,255)))
        paint=ImageDraw.Draw(img,"RGBA")
        for sx,sy,r,seed in specks:
            alpha=round(82*(.5+.5*math.cos(phase+seed)))
            paint.ellipse((sx-r,sy-r,sx+r,sy+r),fill=(225,229,255,alpha))
        frame=np.asarray(img,dtype=np.float32)
        frame+=grain[:,:,None]
        encoder.stdin.write(np.uint8(np.clip(frame,0,255)).tobytes())
    encoder.stdin.close()
    if encoder.wait(): raise RuntimeError("ffmpeg render failed")
    print(f"Rendered text-free Spotify Canvas: {OUTPUT} ({OUTPUT.stat().st_size} bytes, {FRAMES/FPS:g}s)")

if __name__=="__main__":
    main()
