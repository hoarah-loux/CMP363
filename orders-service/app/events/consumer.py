import asyncio
import json
import logging
from typing import Any, Dict

from app.core.config import settings
from app.db.session import _async_session
from app.services.user_snapshot_service import upsert_snapshot


async def process_user_event(session, event: Dict[str, Any]) -> None:
    """Process a user.* event using an existing AsyncSession.

    event: { "type": "user.created" | "user.updated" | "user.deleted", "payload": {...} }
    """
    etype = event.get("type")
    payload = event.get("payload", {})
    if etype in ("user.created", "user.updated"):
        user_id = payload.get("id")
        await upsert_snapshot(session, user_id=user_id, email=payload.get("email"), full_name=payload.get("full_name"))
    elif etype == "user.deleted":
        # For deleted, we remove snapshot if present
        user_id = payload.get("id")
        await session.execute("DELETE FROM user_snapshot WHERE user_id = :uid", {"uid": user_id})
        await session.commit()


async def _consume_message(message) -> None:
    # Incoming message is provided by aio-pika; treat it as an object with .process() and .body
    async with message.process(ignore_processed=True):
        body = message.body.decode()
        try:
            ev = json.loads(body)
        except Exception:
            return
        # open DB session and process
        async with _async_session() as session:
            await process_user_event(session, ev)


async def run_consumer() -> None:
    """Connect to RabbitMQ and consume user events, running until cancelled."""
    try:
        import aio_pika
        from aio_pika import ExchangeType
    except Exception:
        # aio-pika not installed or RabbitMQ unavailable in test environments; do not run consumer
        return
    url = settings.RABBITMQ_URL
    exchange_name = settings.RABBITMQ_EXCHANGE

    # Try to connect to RabbitMQ; if it fails, log and disable the consumer
    try:
        connection = await aio_pika.connect_robust(url)
    except Exception as exc:  # pragma: no cover - runtime network failures
        logging.getLogger(__name__).warning(
            "RabbitMQ connect failed; consumer disabled: %s", exc
        )
        return

    try:
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(exchange_name, ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue("orders.user.events", durable=True)
            await queue.bind(exchange, "user.*")
            await queue.consume(_consume_message)
            # Keep running
            while True:
                await asyncio.sleep(1)
    except Exception as exc:  # pragma: no cover - runtime failures while consuming
        logging.getLogger(__name__).warning("RabbitMQ consumer stopped with error: %s", exc)
        return
