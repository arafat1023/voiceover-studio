import json
from pathlib import Path

import pytest

from studio.config import Project


@pytest.fixture
def make_project(tmp_path: Path):
    """A project folder with the given project.json, loaded as a Project."""
    def make(data: dict | None = None) -> Project:
        (tmp_path / 'project.json').write_text(json.dumps(data or {}), encoding='utf-8')
        return Project.load(tmp_path)
    return make
