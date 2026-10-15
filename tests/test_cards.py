from studio.cards import card_html, map_html


def test_process_map_numbers_follow_the_language():
    assert '<span class="n">১</span>' in map_html('Title', ['A', 'B'], 1, 'bn')
    assert '<span class="n">1</span>' in map_html('Title', ['A', 'B'], 1, 'en')


def test_process_map_lights_steps_up_to_the_current_one():
    html = map_html('Title', ['A', 'B', 'C'], 2, 'en')
    assert html.count('step on') == 2 and html.count('step off') == 1 and html.count(' now') == 1


def test_card_shows_the_credit_only_when_given(make_project):
    project = make_project()
    assert 'class="credit"' in card_html(project, 'Heading', 'Sub', 'Voice credit')
    assert 'class="credit"' not in card_html(project, 'Heading', 'Sub')
