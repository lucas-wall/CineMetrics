"""
Producer de eventos de streaming sintéticos (play/pause/stop/seek/complete/buffer).

Simula o player do CineMetrics publicando eventos JSON no tópico Kafka
'streaming_events'. É a fonte de dados em TEMPO REAL do pipeline.
"""
import os
import json
import time
import random
import datetime as dt

from kafka import KafkaProducer
from faker import Faker

BOOT = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_EVENTS", "streaming_events")
EPS = int(os.getenv("EVENTS_PER_SECOND", "20"))

fake = Faker()
EVENT_TYPES = ["play", "pause", "stop", "seek", "complete", "buffer"]
EVENT_WEIGHTS = [40, 15, 10, 10, 15, 10]
DEVICES = ["web", "mobile_ios", "mobile_android", "smart_tv"]
QUALITIES = ["480p", "720p", "1080p", "4k"]


def make_event():
    return {
        "event_id": fake.uuid4(),
        "user_id": f"U{random.randint(1, 610)}",       # userId range do ml-latest-small
        "movie_id": random.randint(1, 193609),          # movieId range do ml-latest-small
        "event_type": random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0],
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "device": random.choice(DEVICES),
        "playback_position_seconds": random.randint(0, 7200),
        "video_quality": random.choice(QUALITIES),
    }


def main():
    producer = None
    for attempt in range(1, 31):
        try:
            producer = KafkaProducer(
                bootstrap_servers=BOOT,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                linger_ms=50,
            )
            break
        except Exception as e:  # noqa: BLE001
            print(f"[producer] kafka indisponível ({e}); tentativa {attempt}/30", flush=True)
            time.sleep(3)
    if producer is None:
        raise SystemExit("[producer] não conectou ao Kafka")

    print(f"[producer] enviando ~{EPS} ev/s para {BOOT} topic={TOPIC}", flush=True)
    sent = 0
    while True:
        for _ in range(EPS):
            producer.send(TOPIC, make_event())
            sent += 1
        producer.flush()
        if sent % (EPS * 5) == 0:
            print(f"[producer] {sent} eventos enviados", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
