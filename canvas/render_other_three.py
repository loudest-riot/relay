#!/usr/bin/env python3
"""Render 3 distinct letter-free Spotify Canvas loops from the artist's official cover art.

For the 4th song, use approved KINETIC Slight Chance of Misery clip.
Source covers: assets/{crossed-by-stars,hines-001,hines-002,misery}.jpg.
No release-title, brand, or cover-art words may appear in rendered frames.
"""
from pathlib import Path
import math, subprocess
import numpy as np
import cv2
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"assets"
OUT=ROOT/"canvas"/"export"/"four-song"
OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,FRAMES=720,1280,24,144
YY,XX=np.mgrid[0:H,0:W].astype(np.float32)
TAU=2*math.pi

def load(name, rect):
    """Make vertical image from a prevalidated region with NO source typography."""
    im=Image.open(DIR/name).convert("RGB")
    a,b,c,d=rect
    sx,sy=im.size
    im=im.crop((int(a*sx/512),int(b*sy/512),int(c*sx/512),int(d*sy/512)))
    wi,hi=im.size
    scale=max((W+110)/wi,(H+140)/hi)
    nw,nh=int(wi*scale)+2,int(hi*scale)+2
    im=im.resize((nw,nh),Image.Resampling.LANCZOS)
    ox=(nw-W)//2;oy=(nh-H)//2
    return np.asarray(im.crop((ox,oy,ox+W,oy+H)),dtype=np.float32)

# Completely text-free crops: title letters are in the LEFT portion for both
# Crossed and Relay 001; Relay 002 title is at upper left.
crossed=load("crossed-by-stars.jpg",(315,5,510,508))
relay1=load("hines-001.jpg",(313,2,510,510))
relay2=load("hines-002.jpg",(0,130,510,508))
# The leading letters of "MISERY" occupy x <= 385. Use the far right only.
storm=load("misery.jpg",(405,8,510,510))

def warp(image,ph,scale_amp=0.055,panx=20,pany=24,skew=0):
    """Periodic camera breathing, stronger than the earlier near-static renders."""
    zoom=1.045+scale_amp*(.5+.5*math.cos(ph+.12))
    xpan=panx*math.sin(ph+.30)
    ypan=pany*math.cos(ph+.21)
    M=np.array([[zoom,skew*math.sin(ph),-W*(zoom-1)/2+xpan],
                [-skew*math.sin(ph),zoom,-H*(zoom-1)/2+ypan]],np.float32)
    return cv2.warpAffine(image,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

def add_glow(canvas,cx,cy,radx,rady,rgb,strength):
    distance=((XX-cx)/radx)**2+((YY-cy)/rady)**2
    glow=np.exp(-distance*2.7).astype(np.float32)[:,:,None]
    return canvas+glow*np.asarray(rgb,np.float32)[None,None,:]*strength

def wave_reflection(frame,ph,strength=18):
    """Simulated water ripple below horizon, moving along parallel natural bands."""
    horizon=int(H*.49)
    lower=frame[horizon:].copy()
    band=YY[horizon:]
    displacement=(np.sin(band*.092+ph*1.0)+.45*np.cos(band*.153-ph))*strength*np.clip((band-horizon)/(H-horizon),0,1)
    map_x=(XX[horizon:]+displacement).astype(np.float32)
    map_y=YY[horizon:].astype(np.float32)-horizon
    frame[horizon:]=cv2.remap(lower,map_x,map_y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT101)
    return frame

def aurora_streak(frame,ph,mode):
    """One dominant light trace with a visual journey, not random scattered stars."""
    u=.5-.5*math.cos(ph)
    if mode=="crossed":
        # A blue-white slash glides across the lake from far shore then recedes.
        x0=W*(.34+.27*math.sin(ph+.3))
        y0=H*(.17+.36*u)
        rad=(13+17*u)
        frame=add_glow(frame,x0,y0,190+60*u,270+100*u,(18,47,96),.56)
        frame=add_glow(frame,x0,y0,rad*3,rad*3,(72,144,255),.9)
        frame=add_glow(frame,x0,y0,rad*.7,rad*.7,(150,196,246),.95)
        # The water answers the flare.
        reflected_y=H*.72+48*math.sin(ph)
        frame=add_glow(frame,x0,reflected_y,125,200,(62,85,162),.40)
    elif mode=="relay1":
        # A passing warm headlight probes a deep tree corridor.
        x0=W*(.67-.29*u)
        y0=H*(.22+.45*u)
        size=9+23*u
        frame=add_glow(frame,x0,y0,205+40*u,260+40*u,(66,27,8),.77)
        frame=add_glow(frame,x0,y0,size*4,size*4,(255,116,24),.85)
        frame=add_glow(frame,x0,y0,size,size,(250,193,89),.9)
    elif mode=="relay2":
        # A moving sunset reflection creates unmistakable motion without decoration.
        x0=W*(.3+.27*math.sin(ph+.5))
        frame=add_glow(frame,x0,H*.43,240,170,(107,23,10),.52)
        for i in range(7):
            yy=H*(.58+i*.055)
            oscillation=45*math.sin(ph+1.2*i)
            frame=add_glow(frame,x0+oscillation,yy,210-i*10,10+i*2,(255,82+10*i,35+4*i),.19)
    return frame

def frame_for(track,ph):
    if track=="crossed-by-stars":
        a=warp(crossed,ph,.065,22,34)
        b=warp(relay2,ph+.9,.038,15,18)
        # Night lake & stars retained from original art with no album lettering.
        f=a*.75 + b*.25
        f*=np.array([.81,.86,1.11],np.float32)[None,None,:]
        f=wave_reflection(f,ph,14)
        f=aurora_streak(f,ph,"crossed")
    elif track=="hines-park-relay-001":
        a=warp(relay1,ph,.077,35,24)
        b=warp(relay2,ph+.55,.058,20,22)
        # The tight tree perspective lends the sensation of traveling into the woods.
        f=a*.74+b*.26
        f*=np.array([1.03,.86,.84],np.float32)[None,None,:]
        f=aurora_streak(f,ph,"relay1")
    else:
        a=warp(relay2,ph,.060,25,26)
        b=warp(storm,ph+.35,.036,9,10)
        f=a*.83+b*.17
        f*=np.array([1.10,.88,1.03],np.float32)[None,None,:]
        f=wave_reflection(f,ph,24)
        f=aurora_streak(f,ph,"relay2")
    # Higher contrast at the edge of frame, vivid midtones, subtle texture.
    vignette=1-.19*(((XX-W/2)/(W*.76))**2+((YY-H*.51)/(H*.9))**2)
    f *= np.clip(vignette,.70,1)[:,:,None]
    texture=(np.sin(XX*.271+YY*.137)+np.sin(XX*.817-YY*.247))*1.3
    f+=texture[:,:,None]
    return np.uint8(np.clip(f,0,255))

def encode(track):
    output=OUT/(track+".mp4")
    command=["ffmpeg","-y","-loglevel","error",
        "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","-",
        "-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
        "-movflags","+faststart",str(output)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for index in range(FRAMES):
        ph=TAU*index/FRAMES
        proc.stdin.write(frame_for(track,ph).tobytes())
    proc.stdin.close()
    result=proc.wait()
    if result:raise RuntimeError(f"ffmpeg exited {result} for {track}")
    print(f"FINISHED: {output} ({output.stat().st_size} bytes)",flush=True)
    return output

if __name__=="__main__":
    for track in ("crossed-by-stars","hines-park-relay-001","hines-park-relay-002"):
        encode(track)
