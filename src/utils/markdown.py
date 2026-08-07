import html
import re

_HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+)$")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_CODE_RE = re.compile(r"`([^`\n]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def to_telegram_html(text: str) -> str:
    """Конвертирует GitHub-разметку LLM в HTML-разметку Telegram."""
    text = text.replace("\\*", "*").replace("\\_", "_")
    text = html.escape(text)
    text = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = _CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD_RE.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    text = _ITALIC_RE.sub(lambda m: f"<i>{m.group(1)}</i>", text)
    text = _HEADING_RE.sub(lambda m: f"<b>{m.group(2)}</b>", text)
    return text.strip()
