import json
from typing import Any, Dict

from app.core.config import settings


async def publish_user_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Publish a user.{event_type} event with JSON payload to the configured RabbitMQ exchange.

    This function is best-effort: if aio-pika isn't installed or RabbitMQ is unavailable, it logs and returns
    without raising so callers (e.g., user creation) do not fail.
    """
    try:
        import aio_pika
    except Exception:
        # aio-pika not installed during tests or lightweight environments; no-op
        return

    url = settings.RABBITMQ_URL
    exchange_name = settings.RABBITMQ_EXCHANGE

    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
        routing_key = f"user.{event_type}"
        body = json.dumps(payload).encode()
        await exchange.publish(aio_pika.Message(body=body), routing_key=routing_key)
