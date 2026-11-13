#!/bin/bash
# Android capture helper for promo screens (adb over USB or Wi-Fi).
#
#   promo/tools/android.sh devices                      list devices (pick one with ANDROID_SERIAL=...)
#   promo/tools/android.sh launch <package>             bring an app to the front
#   promo/tools/android.sh dump                         list on-screen text/labels with their bounds
#   promo/tools/android.sh tap "<text>"                 tap the first element whose text/label contains <text>
#   promo/tools/android.sh shot <out.png>               full-resolution screenshot
#   promo/tools/android.sh crop <in.png> <out.jpg> [top] [bottom]
#                                                       cut the status bar (default 128 px) and home-bar area (0)
#   promo/tools/android.sh rec <out.mp4> <seconds>      screen recording (runs in the background, returns at once)
#   promo/tools/android.sh frames <in.mp4> <dir> <start> <secs> [top]
#                                                       recording -> dir/f001.jpg… at 30 fps, status bar cropped
#
# Rules (see docs/PROMO.md "Screens"):
# - Only touch apps and accounts the user asked you to. If the phone shows another app, stop: the user is using it.
# - Never save, post or send anything in the app unless the user said so; dismiss "save?" prompts without saving.
# - Real people's names on public screens (leaderboards, members) must be blurred or replaced with demo data.
# - If two entries list the same phone (USB + Wi-Fi), set ANDROID_SERIAL to one of them.
set -e
xml() { adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; adb shell cat /sdcard/ui.xml; }
case "$1" in
  devices) adb devices -l ;;
  launch) adb shell monkey -p "$2" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep 3
          adb shell dumpsys window | grep -m1 mCurrentFocus ;;
  dump) xml | python3 -I -c '
import re, sys
for n in re.findall(r"<node [^>]*>", sys.stdin.read()):
    t = re.search(r"text=\"([^\"]*)\"", n).group(1) or re.search(r"content-desc=\"([^\"]*)\"", n).group(1)
    if t: print(repr(t[:70]), re.search(r"bounds=\"([^\"]*)\"", n).group(1))' ;;
  tap) xy=$(xml | python3 -I -c '
import re, sys
want = sys.argv[1]
for n in re.findall(r"<node [^>]*>", sys.stdin.read()):
    t = re.search(r"text=\"([^\"]*)\"", n).group(1) + "|" + re.search(r"content-desc=\"([^\"]*)\"", n).group(1)
    if want in t:
        a, b, c, d = map(int, re.findall(r"\d+", re.search(r"bounds=\"([^\"]*)\"", n).group(1)))
        print((a + c) // 2, (b + d) // 2); break' "$2")
       if [ -z "$xy" ]; then echo "NOT FOUND: $2" >&2; exit 1; fi
       adb shell input tap $xy; echo "tapped '$2' at $xy" ;;
  shot) adb exec-out screencap -p > "$2"; echo "saved $2" ;;
  crop) top=${4:-128}; bot=${5:-0}
        ffmpeg -y -v error -i "$2" -vf "crop=iw:ih-$top-$bot:0:$top" -q:v 2 "$3"; echo "cropped -> $3" ;;
  rec) (adb shell screenrecord --bit-rate 20000000 --time-limit "$3" /sdcard/promo_rec.mp4 &)
       echo "recording ${3}s… pull with: adb pull /sdcard/promo_rec.mp4 $2  (after it ends)" ;;
  frames) top=${6:-128}; mkdir -p "$3"
          ffmpeg -y -v error -ss "$4" -t "$5" -i "$2" -vf "crop=iw:ih-$top:0:$top,fps=30,scale=720:-2" -q:v 3 "$3/f%03d.jpg"
          echo "$(ls "$3" | wc -l | tr -d ' ') frames in $3 (use in timeline: \"frames\": {\"dir\": \"…\", \"count\": N})" ;;
  *) sed -n 2,21p "$0"; exit 1 ;;
esac
