import pytest

from studio.build import BOX_EARLY, SHOT_EARLY, Builder

PHRASES = [
    {'text': 'The course list shows every course.', 'start': 0.0, 'end': 2.0},
    {'text': 'Click the course button to add one.', 'start': 2.3, 'end': 4.3},
]


@pytest.fixture
def builder(make_project):
    return Builder(make_project())


def test_anchor_time_interpolates_within_the_phrase():
    time, cursor = Builder.anchor_time(PHRASES, 'Click', (0, 0))
    assert time == pytest.approx(2.3)
    assert cursor == (1, 1)


def test_repeated_words_match_in_order():
    first, cursor = Builder.anchor_time(PHRASES, 'course', (0, 0))
    second, cursor = Builder.anchor_time(PHRASES, 'course', cursor)
    third, _ = Builder.anchor_time(PHRASES, 'course', cursor)
    assert first < second < third
    assert first < 2.0 <= third


def test_missing_anchor_is_an_error():
    with pytest.raises(ValueError, match='not found'):
        Builder.anchor_time(PHRASES, 'invoice', (0, 0))


def test_resolve_cues_builds_shots_and_boxes(builder):
    cues = [
        {'at': None, 'shot': 'scene-02a'},
        {'at': 'every course', 'box': [10, 10, 100, 50]},
        {'at': 'Click', 'shot': 'scene-02b', 'box': [20, 20, 80, 40]},
        {'at': 'add one', 'clear': True},
    ]
    segments = builder.resolve_cues(cues, PHRASES, scene_seconds=6.0)
    assert [s['shot'] for s in segments] == ['scene-02a', 'scene-02b']
    click = builder.lead + 2.3
    assert segments[0]['end'] == pytest.approx(click - SHOT_EARLY)
    assert segments[1]['start'] == pytest.approx(click - SHOT_EARLY)
    assert segments[1]['end'] == 6.0
    box = segments[1]['boxes'][0]
    assert box['box'] == [20, 20, 80, 40]
    assert box['start'] == pytest.approx(click - BOX_EARLY)
    assert box['end'] < 6.0  # cleared at "add one"


def test_check_reports_missing_scenes_and_anchors(builder):
    cues = {'1': [{'at': None, 'shot': 'card/title'}, {'at': 'nowhere', 'box': [0, 0, 1, 1]}]}
    problems = builder.check(cues, {1: PHRASES, 2: PHRASES})
    assert any('scene 1' in p and 'nowhere' in p for p in problems)
    assert 'scene 2: no cues' in problems


def test_caption_lines_respect_the_width(builder):
    text = 'The voice is generated phrase by phrase, and the captions and highlights are timed to it automatically.'
    lines = builder.caption_lines(text)
    assert len(lines) > 1
    assert all(len(line) <= builder.caption_max for line in lines)
    assert ' '.join(lines).split() == text.split()
