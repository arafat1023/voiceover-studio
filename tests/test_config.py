from pathlib import Path

from studio.config import STUDIO_ROOT


def test_defaults_are_bangla(make_project):
    project = make_project()
    assert project.language == 'bn'
    assert project.font == 'Kalpurush'
    assert project.voice == STUDIO_ROOT / 'voices' / 'speaker-00737'


def test_english_uses_a_latin_font(make_project):
    assert make_project({'language': 'en'}).font == 'Arial'


def test_output_defaults_to_the_project_folder(make_project):
    project = make_project()
    assert project.output == project.root / 'video.mp4'


def test_relative_output_is_inside_the_project(make_project):
    project = make_project({'output': 'out/demo.mp4'})
    assert project.output == project.root / 'out' / 'demo.mp4'


def test_home_and_absolute_outputs_are_kept(make_project, tmp_path):
    assert make_project({'output': '~/x.mp4'}).output == Path.home() / 'x.mp4'
    absolute = str(tmp_path / 'abs.mp4')
    assert make_project({'output': absolute}).output == Path(absolute)


def test_relative_voice_is_under_the_repo(make_project):
    assert make_project({'voice': 'voices/alice'}).voice == STUDIO_ROOT / 'voices' / 'alice'
