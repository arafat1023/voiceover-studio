#!/bin/bash
# promo/tools/file_takes.sh <project-dir> <label> [voice-name]
#
# After generating a line on the ElevenLabs website (2 takes, both downloaded), move the two newest
# downloads into <project>/vo/<label>-a.mp3 and -b.mp3 and print their lengths.
# Checks both files come from the same generation (same timestamp in the name) so takes never mix.
#   promo/tools/file_takes.sh projects/myapp-promo L03 Shahriar
set -e
dir="$1"; label="$2"; voice="${3:-}"; dl="${DOWNLOADS:-$HOME/Downloads}"
[ -z "$label" ] && { sed -n 2,8p "$0"; exit 1; }
sleep 3   # let the browser finish writing the second file
mkdir -p "$dir/vo"
mapfile_compat() { ls -t "$dl"/ElevenLabs_*${voice}*.mp3 2>/dev/null | head -2; }
IFS=$'\n' files=($(mapfile_compat)); unset IFS
[ ${#files[@]} -lt 2 ] && { echo "Need 2 ElevenLabs downloads in $dl (found ${#files[@]})." >&2; exit 1; }
ta=$(basename "${files[1]}" | grep -oE "T[0-9_]{8}"); tb=$(basename "${files[0]}" | grep -oE "T[0-9_]{8}")
[ "$ta" != "$tb" ] && { echo "The two newest downloads are from different generations ($ta vs $tb); not moving." >&2; exit 1; }
mv "${files[1]}" "$dir/vo/$label-a.mp3"; mv "${files[0]}" "$dir/vo/$label-b.mp3"
for s in a b; do printf "%s-%s %ss\n" "$label" "$s" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$dir/vo/$label-$s.mp3")"; done
