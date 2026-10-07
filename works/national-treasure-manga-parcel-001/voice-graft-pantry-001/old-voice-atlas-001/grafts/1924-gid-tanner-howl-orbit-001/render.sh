#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-./rendered}"
mkdir -p "$OUT"
SRC="$OUT/riley-puckett-1924-source.ogg"
URL="https://upload.wikimedia.org/wikipedia/commons/3/33/Riley_Puckett-Little_Old_Cabin_in_the_Lane.ogg"

curl -L --fail --retry 3 "$URL" -o "$SRC"
sha256sum "$SRC" > "$OUT/source.sha256"

cut_window() {
  local start="$1"
  local end="$2"
  local name="$3"
  ffmpeg -y -hide_banner -loglevel error -ss "$start" -to "$end" -i "$SRC" \
    -af "highpass=f=140,lowpass=f=2800,afftdn=nf=-28,loudnorm=I=-22:TP=-3:LRA=8" \
    -ar 48000 -ac 2 -c:a pcm_s24le "$OUT/$name"
}

cut_window 50 53 howl-window-01.wav
cut_window 87 90 howl-window-02.wav
cut_window 111 114 howl-window-03.wav
cut_window 191 198.1 howl-window-04.wav

ffmpeg -y -hide_banner -loglevel error \
  -i "$OUT/howl-window-01.wav" -i "$OUT/howl-window-02.wav" \
  -i "$OUT/howl-window-03.wav" -i "$OUT/howl-window-04.wav" \
  -filter_complex "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[fossil]" \
  -map "[fossil]" -c:a pcm_s24le -ar 48000 "$OUT/gid-tanner-howl-fossil.wav"

ffmpeg -y -hide_banner -loglevel error -i "$OUT/gid-tanner-howl-fossil.wav" \
  -filter_complex "[0:a]asplit=4[dry][low][high][pre];[dry]volume=0.74[d];[low]rubberband=tempo=0.78:pitch=0.84,volume=0.31,aecho=0.72:0.36:330|760:0.22|0.12,apulsator=hz=0.11:amount=0.92:offset_l=0.0:offset_r=0.5[l];[high]rubberband=tempo=1.08:pitch=1.16,highpass=f=420,lowpass=f=2400,volume=0.17,adelay=95|35,apulsator=hz=0.23:amount=0.88:offset_l=0.3:offset_r=0.8[h];[pre]areverse,highpass=f=360,lowpass=f=2100,volume=0.09,adelay=140|210[p];[d][l][h][p]amix=inputs=4:normalize=0,stereowiden=delay=14:feedback=0.18:crossfeed=0.08:drymix=0.92,alimiter=limit=0.90,loudnorm=I=-18:LRA=9:TP=-1.5[out]" \
  -map "[out]" -ar 48000 -ac 2 -c:a pcm_s24le "$OUT/gid-tanner-howl-orbit-001.wav"

ffmpeg -y -hide_banner -loglevel error -i "$OUT/gid-tanner-howl-orbit-001.wav" -codec:a libmp3lame -b:a 192k "$OUT/gid-tanner-howl-orbit-001-preview.mp3"
sha256sum "$OUT"/howl-window-*.wav "$OUT/gid-tanner-howl-fossil.wav" "$OUT/gid-tanner-howl-orbit-001.wav" "$OUT/gid-tanner-howl-orbit-001-preview.mp3" > "$OUT/render.sha256"
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT/gid-tanner-howl-orbit-001.wav" > "$OUT/duration.txt"
