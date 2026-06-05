"""Заготовка под платежи. На данный момент — каркас и заглушки.

Планируемые способы оплаты:

1. Visa / MasterCard (через Telegram Payments / Bot API):
   - Получить provider_token у @BotFather (раздел Payments).
   - Создавать LabeledPrice + send_invoice.
   - Слушать pre_checkout_query и successful_payment.
   Документация: https://core.telegram.org/bots/payments

2. Крипта (USDT TRC20 / TON / BTC):
   - Простой вариант: показать адрес кошелька + QR + сумма, попросить прислать
     hash транзакции, админ проверит вручную.
   - Прод-вариант: интеграция с агрегатором (NowPayments, CryptoBot @CryptoBot,
     Cryptomus) — у них вебхуки об оплате, callback в БД.

Когда будем активировать — уберём заглушки и подключим router payments_router в bot/main.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from bot.config import settings


@dataclass
class InvoicePlan:
    title: str
    description: str
    amount_cents: int  # для карт: minor units
    currency: str
    payload: str  # уникальный идентификатор заказа (например, "mockup:42:user:123")


def is_card_payments_enabled() -> bool:
    return bool(settings.payments_provider_token)


def is_crypto_enabled() -> bool:
    return bool(settings.crypto_usdt_trc20)


def crypto_payment_text(plan: InvoicePlan) -> Optional[str]:
    """Возвращает текст с реквизитами для оплаты криптой (заглушка)."""
    if not is_crypto_enabled():
        return None
    amount = plan.amount_cents / 100
    return (
        f"💱 <b>Оплата криптой (USDT в сети TON)</b>\n\n"
        f"Заказ: <b>{plan.title}</b>\n"
        f"Сумма: <b>{amount:.2f} {plan.currency}</b> "
        f"(уточните курс USDT у менеджера)\n\n"
        f"Кошелёк (сеть TON):\n<code>{settings.crypto_usdt_trc20}</code>\n\n"
        "⚠️ Отправляйте только USDT в сети TON (не TRC20/Tron).\n\n"
        "После оплаты пришлите hash транзакции — менеджер сверит и подтвердит."
    )


# Сюда позже добавим: send_card_invoice(...), pre_checkout handler, successful_payment handler.
