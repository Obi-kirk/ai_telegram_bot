import pytest
from sqlalchemy import delete

from src.database.db import session_factory
from src.database.models import CartItem, Order, OrderStatus
from src.services.cart import CartService, OrderService
from src.services.catalog import CatalogService

UNIQ_ID = 77001


@pytest.fixture()
async def cart() -> CartService:
    service = CartService()
    await service.clear(UNIQ_ID)
    async with session_factory() as session:
        await session.execute(delete(Order).where(Order.telegram_id == UNIQ_ID))
        await session.execute(delete(CartItem).where(CartItem.telegram_id == UNIQ_ID))
        await session.commit()
    return service


async def test_catalog_parsed() -> None:
    catalog = CatalogService()
    assert len(catalog.products) == 8
    product = catalog.find("ксв-01")
    assert product is not None
    assert product.title == "Тайга"
    assert product.price == 12_500


def test_catalog_unknown_article() -> None:
    assert CatalogService().find("НЕТ-00") is None


async def test_cart_add_and_format(cart: CartService) -> None:
    result = await cart.add(UNIQ_ID, "КСВ-01", 2)
    assert result == "В корзине: Тайга x2"
    items = await cart.list_items(UNIQ_ID)
    assert len(items) == 1
    assert cart.total(items) == 25_000
    assert "Итого: 25 000 руб." in cart.format(items)


async def test_cart_add_twice_merges(cart: CartService) -> None:
    await cart.add(UNIQ_ID, "КСВ-01")
    await cart.add(UNIQ_ID, "КСВ-01", 2)
    items = await cart.list_items(UNIQ_ID)
    assert len(items) == 1
    assert items[0].qty == 3


async def test_cart_change_qty(cart: CartService) -> None:
    await cart.add(UNIQ_ID, "КСВ-01")
    items = await cart.change_qty(UNIQ_ID, "КСВ-01", 1)
    assert items[0].qty == 2
    items = await cart.change_qty(UNIQ_ID, "КСВ-01", -5)
    assert items[0].qty == 1
    items = await cart.change_qty(UNIQ_ID, "НЕТ-00", 1)
    assert len(items) == 1


async def test_cart_add_unknown_article(cart: CartService) -> None:
    assert "не найден" in await cart.add(UNIQ_ID, "ХХХ-99")


async def test_checkout_creates_order(cart: CartService) -> None:
    await cart.add(UNIQ_ID, "КСВ-01")
    result = await cart.checkout(UNIQ_ID)
    assert "Заказ #" in result
    assert cart.format(await cart.list_items(UNIQ_ID)) == "Корзина пуста."

    orders = await OrderService().list_by_user(UNIQ_ID)
    assert len(orders) == 1
    assert orders[0].total == 12_500
    assert orders[0].status == OrderStatus.PENDING.value


async def test_checkout_empty_cart(cart: CartService) -> None:
    assert "пуста" in await cart.checkout(UNIQ_ID)


async def test_status_empty() -> None:
    orders = await OrderService().list_by_user(77002)
    assert OrderService().format(orders) == "У вас пока нет заказов."
