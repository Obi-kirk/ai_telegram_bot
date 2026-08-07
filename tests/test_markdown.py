from src.utils.markdown import to_telegram_html


class TestToTelegramHtml:
    def test_bold(self) -> None:
        assert to_telegram_html("**жирный**") == "<b>жирный</b>"

    def test_italic(self) -> None:
        assert to_telegram_html("*курсив*") == "<i>курсив</i>"

    def test_code(self) -> None:
        assert to_telegram_html("`код`") == "<code>код</code>"

    def test_link(self) -> None:
        assert to_telegram_html("[сайт](https://example.com)") == (
            '<a href="https://example.com">сайт</a>'
        )

    def test_heading(self) -> None:
        assert to_telegram_html("### Заголовок") == "<b>Заголовок</b>"

    def test_escapes_html(self) -> None:
        assert to_telegram_html("5 < 10 & 3 > 2") == "5 &lt; 10 &amp; 3 &gt; 2"

    def test_mixed(self) -> None:
        result = to_telegram_html("**Тайга** — сталь *AUS-8*\n- пункт один")
        assert result.startswith("<b>Тайга</b> — сталь <i>AUS-8</i>")

    def test_plain_text_unchanged(self) -> None:
        assert to_telegram_html("Простой текст без разметки") == (
            "Простой текст без разметки"
        )
