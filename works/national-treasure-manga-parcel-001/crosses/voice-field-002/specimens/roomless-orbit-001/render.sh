#!/usr/bin/env bash
set -euo pipefail

SCRIPT='Do not mistake the signal for the source. The room is not around us anymore. It is listening from very far away. When the echo returns, do not answer it. It already knows the way home.'
printf '%s\n' "$SCRIPT" > script.txt

# Donor witness used: eSpeak 1.48.15
espeak -v en-us -s 130 -p 42 -a 150 -f script.txt -w donor.wav

# Field renderer witness used: FFmpeg 7.1.5
ffmpeg -y -hide_banner -loglevel error \
  -i donor.wav \
  -f lavfi -i "sine=frequency=47:sample_rate=48000:duration=15.4" \
  -f lavfi -i "sine=frequency=173:sample_rate=48000:duration=15.4" \
  -filter_complex "
[0:a]aresample=48000,highpass=f=75,lowpass=f=10500,volume=1.0,pan=stereo|c0=c0|c1=c0[core];
[0:a]atrim=start=0:end=3.10,asetpts=PTS-STARTPTS,highpass=f=260,lowpass=f=3400,rubberband=pitch=0.988,volume=0.12,pan=stereo|c0=c0|c1=c0,apulsator=hz=0.15:amount=0.98:offset_l=0:offset_r=0.5[p1];
[0:a]atrim=start=3.10:end=5.70,asetpts=PTS-STARTPTS,highpass=f=620,lowpass=f=3600,aphaser=in_gain=0.5:out_gain=0.65:delay=2:decay=0.28:speed=0.45:type=t,volume=0.17,pan=stereo|c0=0.7*c0|c1=0.7*c0,adelay=3100|3100[p2];
[0:a]atrim=start=5.70:end=8.80,asetpts=PTS-STARTPTS,highpass=f=430,lowpass=f=4700,aecho=0.72:0.45:700|1350:0.22|0.10,volume=0.21,pan=stereo|c0=c0|c1=c0,stereowiden=delay=20:feedback=0.30:crossfeed=0.08:drymix=0.75,adelay=5700|5700[p3];
[0:a]atrim=start=8.80:end=12.20,asetpts=PTS-STARTPTS,highpass=f=300,lowpass=f=3900,rubberband=pitch=0.978,volume=0.115,pan=stereo|c0=c0|c1=c0,apulsator=hz=0.32:amount=0.93:offset_l=0.15:offset_r=0.65,adelay=8800|8800[p4];
[0:a]atrim=start=1.02:end=1.72,asetpts=PTS-STARTPTS,highpass=f=780,lowpass=f=2350,rubberband=pitch=1.035,volume=0.22,pan=stereo|c0=0.85*c0|c1=0.25*c0,adelay=1020|1020[a1];
[0:a]atrim=start=3.36:end=3.90,asetpts=PTS-STARTPTS,highpass=f=780,lowpass=f=2250,rubberband=pitch=0.962,volume=0.23,pan=stereo|c0=0.3*c0|c1=0.9*c0,adelay=3360|3360[a2];
[0:a]atrim=start=6.00:end=6.78,asetpts=PTS-STARTPTS,highpass=f=700,lowpass=f=2450,rubberband=pitch=1.025,volume=0.23,pan=stereo|c0=0.75*c0|c1=0.35*c0,adelay=6000|6000[a3];
[0:a]atrim=start=6.85:end=8.30,asetpts=PTS-STARTPTS,areverse,highpass=f=520,lowpass=f=2900,volume=0.13,pan=stereo|c0=0.15*c0|c1=0.8*c0,adelay=5450|5450[pre];
[1:a]volume=0.010,lowpass=f=85,afade=t=out:st=11.7:d=0.5,pan=stereo|c0=c0|c1=c0[h1];
[2:a]volume=0.0035,lowpass=f=650,afade=t=out:st=11.7:d=0.5,pan=stereo|c0=c0|c1=c0,apulsator=hz=0.04:amount=0.65[h2];
[core][p1][p2][p3][p4][a1][a2][a3][pre][h1][h2]amix=inputs=11:normalize=0,alimiter=limit=0.91:attack=5:release=80,apad=pad_dur=1.0,atrim=duration=15.4,loudnorm=I=-17:LRA=8:TP=-1.5[out]
" -map "[out]" -c:a pcm_s24le -ar 48000 roomless-orbit-001.wav
