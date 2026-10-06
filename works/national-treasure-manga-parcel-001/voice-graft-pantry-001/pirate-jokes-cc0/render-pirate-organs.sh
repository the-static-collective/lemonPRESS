#!/usr/bin/env bash
set -euo pipefail
SRC="${1:?usage: render-pirate-organs.sh source.mp3 [outdir]}"
OUT="${2:-./rendered-pirate-organs}"
mkdir -p "$OUT/native" "$OUT/derived"

cut(){
  n="$1"; st="$2"; en="$3"; name="$4"; dur=$(python - <<PY
print(max(0.02,float('$en')-float('$st')-0.06))
PY
)
  ffmpeg -y -hide_banner -loglevel error -ss "$st" -to "$en" -i "$SRC" \
    -af "afade=t=in:st=0:d=0.015,afade=t=out:st=$dur:d=0.06,loudnorm=I=-18:TP=-2:LRA=6" \
    -ar 48000 -c:a pcm_s24le "$OUT/native/${n}-${name}.wav"
}

cut 01 4.68 7.82 shore-later
cut 02 17.18 18.24 hooked
cut 03 25.86 27.22 arrr
cut 04 32.94 35.18 on-sale
cut 05 44.76 46.26 eight-pirates
cut 06 52.44 53.28 rookie
cut 07 59.67 61.03 waved
cut 08 67.74 69.10 nervous-wreck
cut 09 75.28 76.47 buccaneer
cut 10 82.80 84.20 arm-and-a-leg
cut 11 89.92 91.47 eye-to-eye
cut 12 96.34 97.80 take-away-the-p
cut 13 103.78 105.82 on-the-deck
cut 14 111.82 112.80 the-plank
cut 15 119.34 120.84 captain-hooky

ffmpeg -y -hide_banner -loglevel error -i "$OUT/native/03-arrr.wav" -af "rubberband=tempo=0.82:pitch=0.84,highpass=f=80,lowpass=f=4800,aecho=0.72:0.42:260|690:0.25|0.13,stereowiden=delay=16:feedback=0.22:crossfeed=0.08:drymix=0.82,loudnorm=I=-20:TP=-3:LRA=8" -ar 48000 -c:a pcm_s24le "$OUT/derived/16-arrr-ghost-bloom.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/native/02-hooked.wav" -af "rubberband=pitch=0.91,highpass=f=100,lowpass=f=3900,aecho=0.82:0.28:92:0.17,acompressor=threshold=0.12:ratio=2.4:attack=7:release=65,loudnorm=I=-18:TP=-2:LRA=6" -ar 48000 -c:a pcm_s24le "$OUT/derived/17-hooked-deck-body.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/native/09-buccaneer.wav" -af "highpass=f=680,lowpass=f=3100,aphaser=in_gain=0.55:out_gain=0.72:delay=2:decay=0.28:speed=0.47:type=t,loudnorm=I=-20:TP=-3:LRA=5" -ar 48000 -c:a pcm_s24le "$OUT/derived/18-buccaneer-relay.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/native/15-captain-hooky.wav" -filter_complex "[0:a]asplit=3[a][b][c];[a]volume=0.68[a1];[b]rubberband=pitch=0.955,adelay=25|25,volume=0.34[b1];[c]rubberband=pitch=1.045,adelay=43|43,volume=0.30[c1];[a1][b1][c1]amix=inputs=3:normalize=0,stereowiden=delay=15:feedback=0.20:crossfeed=0.08:drymix=0.88,loudnorm=I=-20:TP=-2:LRA=8[out]" -map '[out]' -ar 48000 -c:a pcm_s24le "$OUT/derived/19-captain-hooky-choir-fracture.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/native/11-eye-to-eye.wav" -af "rubberband=tempo=0.72:pitch=0.88,aecho=0.70:0.36:440|980:0.20|0.10,highpass=f=120,lowpass=f=4500,loudnorm=I=-21:TP=-3:LRA=9" -ar 48000 -c:a pcm_s24le "$OUT/derived/20-eye-to-eye-roomless.wav"

sha256sum "$SRC" "$OUT"/native/*.wav "$OUT"/derived/*.wav
