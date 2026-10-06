#!/usr/bin/env bash
set -euo pipefail
SRC="${1:?usage: render-organs.sh source.wav [outdir]}"
OUT="${2:-./rendered-organs}"
mkdir -p "$OUT"

sha256sum "$SRC"

slice () {
  local start="$1" end="$2" name="$3" filter="$4"
  ffmpeg -y -hide_banner -loglevel error -ss "$start" -to "$end" -i "$SRC" \
    -af "$filter" -ar 48000 -c:a pcm_s24le "$OUT/$name"
}

slice 2.144 3.552 01-deep-body.wav "afade=t=in:st=0:d=0.02,afade=t=out:st=1.348:d=0.06,loudnorm=I=-18:TP=-2:LRA=7"
slice 4.618667 4.992 02-grit-edge.wav "afade=t=in:st=0:d=0.01,afade=t=out:st=0.313:d=0.05,loudnorm=I=-20:TP=-3:LRA=5"
slice 6.954667 7.637333 03-mid-rasp.wav "afade=t=in:st=0:d=0.015,afade=t=out:st=0.622:d=0.06,loudnorm=I=-18:TP=-2:LRA=6"
slice 18.752 19.914667 04-low-body.wav "afade=t=in:st=0:d=0.02,afade=t=out:st=1.102:d=0.06,loudnorm=I=-18:TP=-2:LRA=7"
slice 22.357333 25.792 05-long-sustain.wav "afade=t=in:st=0:d=0.03,afade=t=out:st=3.335:d=0.10,loudnorm=I=-18:TP=-2:LRA=8"
slice 37.994667 40.213333 06-tail-body.wav "afade=t=in:st=0:d=0.02,afade=t=out:st=2.119:d=0.10,loudnorm=I=-18:TP=-2:LRA=8"
slice 40.224 40.608 07-air-edge.wav "highpass=f=500,afade=t=in:st=0:d=0.01,afade=t=out:st=0.324:d=0.05,loudnorm=I=-24:TP=-5:LRA=4"

ffmpeg -y -hide_banner -loglevel error -i "$OUT/05-long-sustain.wav" -af "rubberband=tempo=0.68:pitch=0.86,highpass=f=90,lowpass=f=5200,aecho=0.72:0.38:410|930:0.22|0.11,stereowiden=delay=18:feedback=0.25:crossfeed=0.10:drymix=0.8,loudnorm=I=-21:TP=-3:LRA=9" -ar 48000 -c:a pcm_s24le "$OUT/08-ghost-bloom.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/04-low-body.wav" -af "rubberband=pitch=0.93,highpass=f=85,lowpass=f=4300,aecho=0.82:0.26:82:0.16,acompressor=threshold=0.11:ratio=2.2:attack=8:release=70,loudnorm=I=-18:TP=-2:LRA=6" -ar 48000 -c:a pcm_s24le "$OUT/09-deck-body.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/06-tail-body.wav" -filter_complex "[0:a]asplit=3[a][b][c];[a]volume=0.72[a1];[b]rubberband=pitch=0.962,adelay=22|22,volume=0.38[b1];[c]rubberband=pitch=1.038,adelay=39|39,volume=0.32[c1];[a1][b1][c1]amix=inputs=3:normalize=0,stereowiden=delay=14:feedback=0.18:crossfeed=0.1:drymix=0.9,loudnorm=I=-20:TP=-2:LRA=8[out]" -map "[out]" -ar 48000 -c:a pcm_s24le "$OUT/10-choir-fracture.wav"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/03-mid-rasp.wav" -af "highpass=f=620,lowpass=f=3200,aphaser=in_gain=0.55:out_gain=0.7:delay=2:decay=0.25:speed=0.42:type=t,volume=0.9,loudnorm=I=-20:TP=-3:LRA=5" -ar 48000 -c:a pcm_s24le "$OUT/11-relay-rasp.wav"

sha256sum "$OUT"/*.wav
