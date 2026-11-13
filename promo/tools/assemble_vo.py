#!/usr/bin/env python3
"""Place voice-over lines on the promo timeline and build the audio.

    python3 promo/tools/assemble_vo.py <project-dir> [--tail 3.5] [--no-master]

Reads <project>/timeline.json. Each scene with a voice line names its file and the pause before it:
    { "type": "feature", "voice": "vo/L05-a.mp3", "gapBefore": 0.8, ... }
For every such scene this script:
  1. trims leading/trailing silence and applies a light voice master (EQ, de-ess, compression),
  2. places it after the previous line plus gapBefore (default 0.6 s; the first line starts at gapBefore),
  3. writes the measured "start" and "dur" back into timeline.json, and "total" (last line + --tail).
Scenes without "voice" keep their start/dur (use them for silent beats, e.g. a recitation clip you
place with "audioClip": {"file": "...", "at": 0.0} — it is mixed in at the scene start + at).

Outputs: audio/voice_only.wav (voice + clips, -14 LUFS) and audio/mix.wav. If audio/sfx.wav exists it is
ducked under the voice (sidechain) in mix.wav; otherwise mix.wav is the voice track.
Only ffmpeg/ffprobe are needed. Python 3.9+.
"""
import json, subprocess, sys, os

def ff(*a):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *a], check=True)

def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                                capture_output=True, text=True, check=True).stdout)

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    d = args[0]; tail = float(args[args.index('--tail') + 1]) if '--tail' in args else 3.5
    master = '--no-master' not in args
    tl_path = os.path.join(d, 'timeline.json'); tl = json.load(open(tl_path, encoding='utf8'))
    os.makedirs(os.path.join(d, 'audio', 'lines'), exist_ok=True)
    chain = ('highpass=f=75,equalizer=f=140:t=q:w=1.0:g=2.5,equalizer=f=320:t=q:w=1.2:g=-2,'
             'equalizer=f=3500:t=q:w=1.0:g=2,highshelf=f=9000:g=1.5,deesser=i=0.4,'
             'acompressor=threshold=-20dB:ratio=3:attack=8:release=150:makeup=2.5') if master else 'anull'
    trim = ('silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,'
            'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse')
    t = 0.0; inputs = []; delays = []
    for i, s in enumerate(tl['scenes']):
        if 'voice' in s:
            src = os.path.join(d, s['voice']); out = os.path.join(d, 'audio', 'lines', f's{i + 1:02d}.wav')
            ff('-i', src, '-af', f'{trim},{chain}', '-ar', '48000', '-ac', '1', out)
            t += float(s.get('gapBefore', 0.6))
            s['start'] = round(t, 3); s['dur'] = round(dur(out), 3); t += s['dur']
            inputs.append(out); delays.append(s['start'])
        else:
            t = max(t, s['start'] + s['dur'])
        clip = s.get('audioClip')
        if clip:
            inputs.append(os.path.join(d, clip['file'])); delays.append(s['start'] + float(clip.get('at', 0)))
    if not inputs:
        sys.exit('No scene has a "voice" file.')
    tl['total'] = round(t + tail, 2)
    json.dump(tl, open(tl_path, 'w', encoding='utf8'), ensure_ascii=False, indent=1)

    cmd = []; flt = []
    for k, (f, at) in enumerate(zip(inputs, delays)):
        cmd += ['-i', f]; ms = int(at * 1000); flt.append(f'[{k}]aresample=48000,aformat=channel_layouts=mono,adelay={ms}|{ms}[a{k}]')
    flt.append(''.join(f'[a{k}]' for k in range(len(inputs))) + f'amix=inputs={len(inputs)}:normalize=0,apad=whole_dur={tl["total"]}[v]')
    voice_raw = os.path.join(d, 'audio', 'voice_raw.wav')
    ff(*cmd, '-filter_complex', ';'.join(flt), '-map', '[v]', '-t', str(tl['total']), voice_raw)
    voice = os.path.join(d, 'audio', 'voice_only.wav'); mix = os.path.join(d, 'audio', 'mix.wav')
    ff('-i', voice_raw, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9', '-ar', '48000', '-ac', '2', voice)
    sfx = os.path.join(d, 'audio', 'sfx.wav')
    if os.path.exists(sfx):
        ff('-i', voice_raw, '-i', sfx, '-filter_complex',
           '[0]aresample=48000,asplit=2[vo][sc];[1]aresample=48000,volume=0.85[fx];'
           '[fx][sc]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=300[fxd];'
           '[vo][fxd]amix=inputs=2:normalize=0:duration=first,'
           'acompressor=threshold=-18dB:ratio=2.5:attack=10:release=150,loudnorm=I=-14:TP=-1.0:LRA=8',
           '-ar', '48000', '-ac', '2', mix)
    else:
        ff('-i', voice, '-c', 'copy', mix)
    os.remove(voice_raw)
    for s in tl['scenes']:
        if 'voice' in s:
            print(f"{s['start']:7.2f}s  {s['dur']:5.2f}s  {s['voice']}")
    print(f"total {tl['total']}s -> timeline.json, audio/voice_only.wav, audio/mix.wav")

if __name__ == '__main__':
    main()
