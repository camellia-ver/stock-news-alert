# html_utils.py
import html
from html.parser import HTMLParser


class _HTMLStripper(HTMLParser):  
    SKIP_TAGS = {"script", "style", "head"}

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        super().reset()
        self._skip_depth: int = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return html.unescape(" ".join(self._parts))


def strip_html(text: str) -> str:
    """HTML 태그와 entities를 제거하고 순수 텍스트를 반환합니다."""
    if not text:
        return text
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()