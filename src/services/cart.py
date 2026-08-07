from sqlalchemy import delete, select

from src.database.db import session_factory
from src.database.models import CartItem, Order, OrderStatus
from src.services.catalog import CatalogService

STATUS_LABELS = {
    OrderStatus.PENDING.value: "Сборка",
    OrderStatus.CONFIRMED.value: "Подтверждён",
    OrderStatus.SHIPPED.value: "Отправка",
    OrderStatus.DELIVERED.value: "Доставка",
    OrderStatus.RECEIVED.value: "Получен",
}


class CartService:
    """Корзина пользователя: добавление, просмотр, очистка, оформление заказа."""

    def __init__(self, catalog: CatalogService | None = None) -> None:
        self.catalog = catalog or CatalogService()

    async def add(self, telegram_id: int, article: str, qty: int = 1) -> str:
        product = self.catalog.find(article)
        if product is None:
            return f"Товар с артикулом {article.upper()} не найден."
        async with session_factory() as session:
            stmt = select(CartItem).where(
                CartItem.telegram_id == telegram_id,
                CartItem.article == product.article.upper(),
            )
            item = (await session.execute(stmt)).scalar_one_or_none()
            if item:
                item.qty += qty
                item.title = product.title
                item.price = product.price
            else:
                session.add(
                    CartItem(
                        telegram_id=telegram_id,
                        article=product.article.upper(),
                        title=product.title,
                        price=product.price,
                        qty=qty,
                    )
                )
            await session.commit()
        return f"В корзине: {product.title} x{qty}"

    async def list_items(self, telegram_id: int) -> list[CartItem]:
        stmt = select(CartItem).where(CartItem.telegram_id == telegram_id)
        async with session_factory() as session:
            return list((await session.execute(stmt)).scalars().all())

    async def change_qty(
        self, telegram_id: int, article: str, delta: int
    ) -> list[CartItem]:
        stmt = select(CartItem).where(
            CartItem.telegram_id == telegram_id,
            CartItem.article == article.upper(),
        )
        async with session_factory() as session:
            item = (await session.execute(stmt)).scalar_one_or_none()
            if item is not None:
                item.qty = max(1, item.qty + delta)
                await session.commit()
        return await self.list_items(telegram_id)

    async def remove(self, telegram_id: int, article: str) -> None:
        stmt = delete(CartItem).where(
            CartItem.telegram_id == telegram_id,
            CartItem.article == article.upper(),
        )
        async with session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    def total(items: list[CartItem]) -> int:
        return sum(item.price * item.qty for item in items)

    def format(self, items: list[CartItem]) -> str:
        if not items:
            return "Корзина пуста."
        lines = [
            f"- {item.title} ({item.article}) x{item.qty} — "
            f"{item.price * item.qty:,} руб.".replace(",", " ")
            for item in items
        ]
        lines.append(f"Итого: {self.total(items):,} руб.".replace(",", " "))
        return "\n".join(lines)

    async def clear(self, telegram_id: int) -> None:
        stmt = delete(CartItem).where(CartItem.telegram_id == telegram_id)
        async with session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def checkout(self, telegram_id: int) -> str | None:
        items = await self.list_items(telegram_id)
        if not items:
            return "Корзина пуста. Добавьте товар: /cart add <артикул>"
        total = self.total(items)
        async with session_factory() as session:
            order = Order(
                telegram_id=telegram_id,
                total=total,
                status=OrderStatus.PENDING.value,
            )
            session.add(order)
            await session.flush()
            order_id = order.id
            await session.execute(
                delete(CartItem).where(CartItem.telegram_id == telegram_id)
            )
            await session.commit()
        return (
            f"Заказ #{order_id} оформлен на {total:,} руб.".replace(",", " ")
            + f"\nСтатус: {STATUS_LABELS[OrderStatus.PENDING.value]}"
        )


class OrderService:
    """Заказы пользователя для команды /status."""

    async def list_by_user(self, telegram_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.telegram_id == telegram_id)
            .order_by(Order.id.desc())
        )
        async with session_factory() as session:
            return list((await session.execute(stmt)).scalars().all())

    async def list_all(self) -> list[Order]:
        stmt = select(Order).order_by(Order.id.desc())
        async with session_factory() as session:
            return list((await session.execute(stmt)).scalars().all())

    async def get(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        async with session_factory() as session:
            return (await session.execute(stmt)).scalar_one_or_none()

    async def set_status(self, order_id: int, status: str) -> Order | None:
        order = await self.get(order_id)
        if order is None:
            return None
        async with session_factory() as session:
            order = (
                await session.execute(select(Order).where(Order.id == order_id))
            ).scalar_one()
            order.status = status
            await session.commit()
        return order

    def format(self, orders: list[Order]) -> str:
        if not orders:
            return "У вас пока нет заказов."
        lines = [
            f"- Заказ #{order.id} — {order.total:,} руб.".replace(",", " ")
            + f" — {STATUS_LABELS.get(order.status, order.status)}"
            for order in orders
        ]
        return "\n".join(lines)
