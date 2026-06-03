from kubernetes import client
from typing import Protocol

from kx.k8s import load_config
from kx.kubectl import normalize_kind


class EventsServiceProtocol(Protocol):
    def get(self, namespace: str) -> list: ...
    def filter(self, events: list, name: str, kind: str) -> list: ...


class EventsService:
    def get(self, namespace: str) -> list:
        load_config()
        v1 = client.CoreV1Api()
        return v1.list_namespaced_event(namespace=namespace).items

    def filter(self, events: list, name: str, kind: str) -> list:
        normalized = normalize_kind(kind)
        return [
            e for e in events
            if e.involved_object.name == name
            and e.involved_object.kind == normalized
        ]
