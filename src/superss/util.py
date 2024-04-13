from typing import List


def load_css_properties() -> List[str]:
    with open('resources/css_properties.txt') as f:
        return f.read().splitlines()


def load_html_elements() -> List[str]:
    with open('resources/css_tags.txt') as f:
        return f.read().splitlines()


def make_keywords_dict(types):
    return {t.value: t for t in types}
