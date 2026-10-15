"""The LANGUAGES option of setup.sh, run on its own (no installs)."""
import re
import subprocess
from pathlib import Path

import pytest

SETUP = Path(__file__).resolve().parent.parent / 'setup.sh'


def parse(env: dict[str, str]) -> subprocess.CompletedProcess:
    text = SETUP.read_text(encoding='utf-8')
    block = re.search(r'^LANGUAGES=.*?^echo "installing: \$LANG_NAMES"$', text, re.S | re.M).group(0)
    script = 'set -euo pipefail\n' + block + '\necho "BN=$HAS_BN EN=$HAS_EN"\n'
    return subprocess.run(['bash', '-c', script], env={'PATH': '/usr/bin:/bin', **env},
                          capture_output=True, text=True, check=False)


@pytest.mark.parametrize('env, expected', [
    ({}, 'installing: Bangla + English\nBN=1 EN=1'),
    ({'LANGUAGES': 'bn'}, 'installing: Bangla\nBN=1 EN=0'),
    ({'LANGUAGES': 'en'}, 'installing: English\nBN=0 EN=1'),
    ({'LANGUAGES': 'en,bn'}, 'installing: Bangla + English\nBN=1 EN=1'),
    ({'WITH_EN': '0'}, 'installing: Bangla\nBN=1 EN=0'),
])
def test_language_choices(env, expected):
    result = parse(env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_unknown_language_is_rejected():
    result = parse({'LANGUAGES': 'fr'})
    assert result.returncode == 1
    assert "unknown language 'fr'" in result.stdout


def test_setup_script_parses():
    assert subprocess.run(['bash', '-n', str(SETUP)], check=False).returncode == 0
