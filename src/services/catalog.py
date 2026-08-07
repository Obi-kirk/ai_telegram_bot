import re
from dataclasses import dataclass

_DATA_PATH = "data/catalog.txt"

_ARTICLE_RE = re.compile(r"Артикул:\s*([\w-]+)")
_PRICE_RE = re.compile(r"Цена:\s*([\d\s]+)\s*руб\.")
_TITLE_RE = re.compile(r'^Модель:\s*"(.+)"\s*(.*)$')


@dataclass
class Product:
    article: str
    title: str
    price: int
    category: str
    description: str = ""


class CatalogService:
    """Парсит catalog.txt в список товаров (кешируется при первом обращении)."""

    def __init__(self, path: str = _DATA_PATH) -> None:
        self.path = path
        self._products: list[Product] | None = None

    def _load(self) -> list[Product]:
        if self._products is not None:
            return self._products
        products: list[Product] = []
        category = ""
        buffer: dict[str, str | int] = {}

        def flush() -> None:
            if "article" in buffer and "title" in buffer and "price" in buffer:
                products.append(
                    Product(
                        article=buffer["article"],
                        title=buffer["title"],
                        price=buffer["price"],
                        category=category,
                        description=" ".join(buffer.get("description", [])),
                    )
                )

        with open(self.path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                if line.startswith("## "):
                    flush()
                    buffer.clear()
                    category = line.removeprefix("## ").split(":", 1)[-1].strip()
                    continue
                if line.startswith("- "):
                    flush()
                    buffer.clear()
                    title = line.removeprefix("- ").strip()
                    match = _TITLE_RE.match(title)
                    if match:
                        title = " ".join(part for part in match.groups() if part)
                    buffer["title"] = title
                    continue
                match = _ARTICLE_RE.search(line)
                if match:
                    buffer["article"] = match.group(1)
                match = _PRICE_RE.search(line)
                if match:
                    buffer["price"] = int(match.group(1).replace(" ", ""))
                if "title" in buffer:
                    buffer.setdefault("description", []).append(line)
        flush()
        self._products = products
        return products

    @property
    def products(self) -> list[Product]:
        return self._load()

    def find(self, article: str) -> Product | None:
        for product in self.products:
            if product.article.upper() == article.strip().upper():
                return product
        return None

    def by_category(self) -> list[tuple[str, list[Product]]]:
        groups: dict[str, list[Product]] = {}
        for product in self.products:
            groups.setdefault(product.category, []).append(product)
        return list(groups.items())

    def format_category(self, category: str, products: list[Product]) -> str:
        lines = [f"{category}"]
        lines.extend(
            f"- {p.title} ({p.article}) — {p.price:,} руб.".replace(",", " ")
            for p in products
        )
        return "\n".join(lines)
