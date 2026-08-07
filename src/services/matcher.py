import re
from dataclasses import dataclass

from src.services.catalog import CatalogService, Product

_BUDGET_RE = re.compile(r"(\d[\d\s]*)\s*(?:руб|₽|тыс)")
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Охотничьи ножи": (
        "охотн",
        "охота",
        "дичь",
        "разделк",
        "шкур",
    ),
    "Туристические ножи": (
        "складн",
        "туризм",
        "турист",
        "поход",
        "едс",
        "повседневн",
        "карманн",
        "город",
    ),
    "Кухонные ножи": (
        "кухон",
        "кухн",
        "шеф",
        "повар",
        "сантоку",
        "нарезк",
        "шинков",
        "готовк",
    ),
    "Ножи для выживания": (
        "выжив",
        "экстрем",
        "рубк",
        "тактическ",
        "поля",
    ),
}
_STEEL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "95X18": ("95x18",),
    "D2": ("d2",),
    "AUS-8": ("aus-8", "aus 8"),
    "VG-10": ("vg-10", "vg10"),
    "440C": ("440c",),
    "CPM-3V": ("cpm-3v", "cpm3v"),
    "дамаск": ("дамаск",),
    "нержавеющая": ("нержаве",),
}
_HANDLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "деревянная": ("дерев", "кап", "бук", "древесин"),
    "текстолит": ("текстолит",),
    "микарта": ("микарт",),
    "кожа": ("кож",),
    "G-10": ("g-10", "g10"),
}
_ACCESSORY_WORDS = (
    "масло",
    "заточк",
    "брусок",
    "набор",
    "аксессуар",
    "уход",
)


@dataclass
class Match:
    product: Product
    score: int


class ProductMatcher:
    """Ищет товары каталога по описанию: бюджет, категория, сталь, рукоять."""

    def __init__(self, catalog: CatalogService | None = None) -> None:
        self.catalog = catalog or CatalogService()

    def parse_budget(self, text: str) -> int | None:
        lowered = text.lower()
        if "тыс" in lowered:
            match = re.search(r"(\d[\d\s]*)\s*тыс", lowered)
            if match:
                return int(match.group(1).replace(" ", "")) * 1000
        match = _BUDGET_RE.search(lowered)
        if match:
            return int(match.group(1).replace(" ", ""))
        return None

    def _category(self, text: str) -> str | None:
        lowered = text.lower()
        for category, keywords in _CATEGORY_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return None

    def _steel(self, text: str) -> str | None:
        lowered = text.lower()
        for steel, keywords in _STEEL_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return steel
        return None

    def _handle(self, text: str) -> str | None:
        lowered = text.lower()
        for handle, keywords in _HANDLE_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return handle
        return None

    def is_product_query(self, text: str) -> bool:
        lowered = text.lower()
        has_criteria = (
            self._category(text) is not None
            or self._steel(text) is not None
            or self._handle(text) is not None
            or self.parse_budget(text) is not None
        )
        has_marker = any(
            word in lowered
            for word in ("нож", "купить", "подойд", "выбрать", "каталог", "модель")
        )
        return has_criteria and has_marker

    def _haystack(self, product: Product) -> str:
        return f"{product.title} {product.category} {product.description}".lower()

    @staticmethod
    def _label_hits(
        mapping: dict[str, tuple[str, ...]], label: str | None, haystack: str
    ) -> bool:
        if label is None:
            return False
        return any(keyword in haystack for keyword in mapping.get(label, ()))

    def score(self, text: str, product: Product) -> int:
        lowered = text.lower()
        haystack = self._haystack(product)
        budget = self.parse_budget(text)
        score = 0
        category = self._category(text)
        if category and category.lower() in product.category.lower():
            score += 3
        if budget is not None:
            score += 3 if product.price <= budget else -3
        if self._label_hits(_STEEL_KEYWORDS, self._steel(text), haystack):
            score += 2
        if self._label_hits(_HANDLE_KEYWORDS, self._handle(text), haystack):
            score += 2
        if (
            product.article.startswith("АКС")
            and "нож" in lowered
            and not any(word in lowered for word in _ACCESSORY_WORDS)
        ):
            score = -10
        return score

    def match(self, text: str, limit: int = 3) -> list[Match]:
        budget = self.parse_budget(text)
        matches = [
            Match(product=p, score=self.score(text, p)) for p in self.catalog.products
        ]
        matches = [m for m in matches if m.score > 0]
        matches.sort(
            key=lambda m: (
                -m.score,
                abs((budget or m.product.price) - m.product.price),
            )
        )
        return matches[:limit]

    def format(self, text: str) -> str | None:
        matches = self.match(text)
        if not matches:
            return None
        budget = self.parse_budget(text)
        header = "По вашему описанию подходят:"
        if budget is not None:
            header += f" (бюджет до {budget:,} руб.)".replace(",", " ")
        lines = [
            f"- {m.product.title} ({m.product.article}) — "
            f"{m.product.price:,} руб.".replace(",", " ")
            for m in matches
        ]
        lines.append("Подробнее: /catalog или нажмите кнопку под категорией.")
        return header + "\n" + "\n".join(lines)
