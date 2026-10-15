import pytest

from studio.narrate import for_voice, read_scenes, split_phrases, word_error


def texts(parts):
    return [text for text, _ in parts]


def test_read_scenes(tmp_path):
    pitch = tmp_path / 'pitch.md'
    pitch.write_text('# Title\n\n### Scene 1: Intro\n**On screen:** card\n**Narration:**\nHello there.\n\n'
                     '### Scene 2: List\n**Narration:**\nFirst line. Second line.\n', encoding='utf-8')
    assert read_scenes(pitch) == {1: 'Hello there.', 2: 'First line. Second line.'}


def test_bangla_splits_on_danda_question_and_colon(make_project):
    project = make_project()
    parts = split_phrases(project, 1, 'আজ আমরা দেখব। কীভাবে? যেমন: এটি।')
    assert texts(parts) == ['আজ আমরা দেখব।', 'কীভাবে?', 'যেমন:', 'এটি।']
    assert parts[2][1] == 0.18  # colon gap
    assert parts[0][1] == 0.32  # sentence gap


def test_english_splits_on_full_stop_but_not_inside_numbers(make_project):
    project = make_project({'language': 'en'})
    assert texts(split_phrases(project, 1, 'It costs 3.5 dollars. Buy it now!')) == ['It costs 3.5 dollars.', 'Buy it now!']


def test_comma_scene_reads_list_items_separately(make_project):
    project = make_project({'language': 'en', 'comma_scenes': [2]})
    parts = split_phrases(project, 2, 'We track income, expenses and salaries.')
    assert texts(parts) == ['We track income,', 'expenses', 'and salaries.']
    assert [gap for _, gap in parts[:-1]] == [0.8, 0.8]


def test_slow_scene_uses_the_longer_gap(make_project):
    project = make_project({'language': 'en', 'slow_scenes': [3]})
    assert split_phrases(project, 3, 'One. Two.')[0][1] == 1.0
    assert split_phrases(project, 4, 'One. Two.')[0][1] == 0.32


def test_pause_before_splits_the_phrase(make_project):
    project = make_project({'pause_before': {'1': 'অনেকটাই স্বয়ংক্রিয়'}})
    parts = split_phrases(project, 1, 'এটি পুরো কাজটিকে অনেকটাই স্বয়ংক্রিয় করে।')
    assert texts(parts) == ['এটি পুরো কাজটিকে', 'অনেকটাই স্বয়ংক্রিয় করে।']
    assert parts[0][1] == 0.5


def test_voice_spellings_change_only_the_spoken_text(make_project):
    project = make_project({'voice_spellings': {'সিএসভি': 'সি-এস-ভি'}})
    assert for_voice(project, 'সিএসভি ফাইল।') == 'সি-এস-ভি ফাইল।'


def test_bangla_refuses_digits_english_allows_them(make_project):
    with pytest.raises(ValueError, match='digits'):
        for_voice(make_project(), 'মোট ৪০০০ টাকা।')
    assert for_voice(make_project({'language': 'en'}), 'Ten 10 minutes.') == 'Ten 10 minutes.'


def test_word_error_identical_text_is_zero():
    assert word_error('Click the new course button.', 'click the new course button') == 0.0


def test_word_error_ignores_unicode_form_of_bangla_letters():
    script = 'এরপর ঠিক করুন কোথা\u09df হাইলাইট হবে।'  # য় as one code point
    heard = 'এরপর ঠিক করুন কোথা\u09af\u09bc হাইলাইট হবে'  # য + nukta, as recognisers often write it
    assert script.rstrip('।') != heard
    assert word_error(script, heard) == 0.0


def test_word_error_accepts_digits_for_number_words():
    assert word_error('The person who reads ten pages a day.', 'The person who reads 10 pages a day') == 0.0


def test_word_error_ignores_spacing_only_differences():
    assert word_error('ভয়েসওভার স্টুডিও দিয়ে।', 'ভয়েস ওভার স্টুডিও দিয়ে') == 0.0


def test_word_error_counts_a_real_mistake():
    assert word_error('Click the new course button.', 'Click the blue course button') == pytest.approx(0.2)
