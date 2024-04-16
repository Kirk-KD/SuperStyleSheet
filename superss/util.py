from typing import List
import pkgutil


def load_css_properties() -> List[str]:
    return pkgutil.get_data(__name__, 'resources/css_properties.txt').decode("utf-8").splitlines()


def load_html_elements() -> List[str]:
    return pkgutil.get_data(__name__, 'resources/css_tags.txt').decode("utf-8").splitlines()


def make_keywords_dict(types):
    return {t.value: t for t in types}
