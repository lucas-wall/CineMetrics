"""
Synthetic streaming event producer (play/pause/stop/seek/complete/buffer).

Simulates the CineMetrics player by publishing JSON events to the Kafka topic
'streaming_events'. It is the REAL-TIME data source of the pipeline.
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
        "user_id": f"U{random.randint(1, 610)}",       # ml-latest-small userId range
        "movie_id": random.randint(1, 193609),          # ml-latest-small movieId range
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
            print(f"[producer] kafka unavailable ({e}); attempt {attempt}/30", flush=True)
            time.sleep(3)
    if producer is None:
        raise SystemExit("[producer] could not connect to Kafka")

    print(f"[producer] sending ~{EPS} ev/s to {BOOT} topic={TOPIC}", flush=True)
    sent = 0
    while True:
        for _ in range(EPS):
            producer.send(TOPIC, make_event())
            sent += 1
        producer.flush()
        if sent % (EPS * 5) == 0:
            print(f"[producer] {sent} events sent", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
