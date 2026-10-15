"""Speak one line in a voice, to test a voice or a pronunciation.

    .venv/bin/python -m studio.speak voices/speaker-00737 "আসসালামু আলাইকুম।" out.wav [--speed 0.9] [--seconds 1.8]
    .venv/bin/python -m studio.speak builtin "Welcome to the demo." out.wav --language en

Tip: generate a hard word several ways (plain, hyphenated "সি-এস-ভি", with ্‌) and pick by ear.
"""
import argparse

import soundfile as sf

from studio.tts import Voice


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('voice', help='voice folder, or "builtin" for the English model\'s own voice')
    parser.add_argument('text')
    parser.add_argument('out')
    parser.add_argument('--language', default='bn', choices=['bn', 'en'])
    parser.add_argument('--speed', type=float, default=0.9)
    parser.add_argument('--seconds', type=float, help='force the clip length (for short phrases)')
    args = parser.parse_args()
    audio, rate = Voice(args.voice, language=args.language).speak(args.text, speed=args.speed, seconds=args.seconds)
    sf.write(args.out, audio, rate)
    print(f'wrote {args.out} ({len(audio) / rate:.1f}s)')


if __name__ == '__main__':
    main()
