"""Project configuration: one folder per video under projects/, described by project.json.

A project folder holds:
    project.json   settings (voice, pacing, cards, insets, output path)
    pitch.md       the script: "### Scene N: ..." blocks, each with a "**Narration:**" paragraph
    cues.json      per scene: which screenshot to show and what to highlight on which phrase
    shots/         screenshots (any width; boxes in cues.json use that screenshot's own pixels)
    assets/        logo and other images used by the cards
Generated (safe to delete): narration/, cards/, work/
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Project:
    root: Path
    data: dict = field(default_factory=dict)

    @classmethod
    def load(cls, folder: str | Path) -> 'Project':
        root = Path(folder).expanduser().resolve()
        data = json.loads((root / 'project.json').read_text(encoding='utf-8'))
        return cls(root, data)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    @property
    def pitch(self) -> Path:
        return self.root / self.get('pitch', 'pitch.md')

    @property
    def cues(self) -> Path:
        return self.root / self.get('cues', 'cues.json')

    @property
    def shots(self) -> Path:
        return self.root / 'shots'

    @property
    def narration(self) -> Path:
        return self.root / 'narration'

    @property
    def cards(self) -> Path:
        return self.root / 'cards'

    @property
    def work(self) -> Path:
        return self.root / 'work'

    @property
    def language(self) -> str:
        """'bn' (Bangla, IndicF5) or 'en' (English, Chatterbox)."""
        return self.get('language', 'bn')

    @property
    def font(self) -> str:
        """Default font for captions and cards: Kalpurush shapes Bangla well; Arial exists on macOS
        and is aliased by fontconfig on Linux (Liberation Sans / DejaVu Sans)."""
        return 'Kalpurush' if self.language == 'bn' else 'Arial'

    @property
    def voice(self) -> Path:
        voice = Path(self.get('voice', 'voices/speaker-00737'))
        return voice if voice.is_absolute() else STUDIO_ROOT / voice

    @property
    def output(self) -> Path:
        return Path(self.get('output', str(self.root / 'video.mp4'))).expanduser()

    def asset(self, name: str) -> Path:
        path = Path(name)
        return path if path.is_absolute() else self.root / path
