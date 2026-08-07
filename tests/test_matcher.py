from src.services.matcher import ProductMatcher

matcher = ProductMatcher()


def test_parse_budget() -> None:
    assert matcher.parse_budget("охотничий нож до 10 000 руб.") == 10_000
    assert matcher.parse_budget("до 10 тыс") == 10_000
    assert matcher.parse_budget("покажи тайгу") is None


def test_is_product_query() -> None:
    assert matcher.is_product_query("охотничий нож до 10 000 руб.")
    assert matcher.is_product_query("складной нож для туризма")
    assert matcher.is_product_query("какой нож с деревянной рукоятью выбрать")
    assert not matcher.is_product_query("как ухаживать за ножом")
    assert not matcher.is_product_query("привет, как дела?")


def test_match_by_budget() -> None:
    matches = matcher.match("нож до 9 000 руб.")
    assert matches
    assert all(m.product.price <= 9_000 for m in matches)
    assert matches[0].product.article == "КСВ-07"


def test_match_by_category() -> None:
    matches = matcher.match("охотничий нож")
    assert matches
    assert all("Охотничьи" in m.product.category for m in matches)


def test_match_by_handle() -> None:
    matches = matcher.match("нож с деревянной рукоятью")
    assert matches
    assert any("Тайга" == m.product.title for m in matches)


def test_match_no_results() -> None:
    assert matcher.match("нож из титана с подсветкой") == []
    assert matcher.format("нож из титана с подсветкой") is None


def test_format_mentions_budget() -> None:
    text = matcher.format("купить нож до 9 000 руб.")
    assert text is not None
    assert "бюджет до 9 000" in text


def test_find_references_by_article() -> None:
    refs = matcher.find_references("сколько стоит КСВ-01?")
    assert [r.article for r in refs] == ["КСВ-01"]


def test_find_references_by_title() -> None:
    refs = matcher.find_references("расскажи про нож Тайга")
    assert any(r.title == "Тайга" for r in refs)


def test_find_references_empty() -> None:
    assert matcher.find_references("привет") == []
