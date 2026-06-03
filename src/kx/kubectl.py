import subprocess
from typing import Protocol

_KIND_MAP = {
    "pod": "Pod", "pods": "Pod",
    "deployment": "Deployment", "deployments": "Deployment", "deploy": "Deployment",
    "replicaset": "ReplicaSet", "replicasets": "ReplicaSet", "rs": "ReplicaSet",
    "statefulset": "StatefulSet", "statefulsets": "StatefulSet", "sts": "StatefulSet",
    "daemonset": "DaemonSet", "daemonsets": "DaemonSet", "ds": "DaemonSet",
    "hpa": "HorizontalPodAutoscaler",
    "horizontalpodautoscaler": "HorizontalPodAutoscaler",
    "horizontalpodautoscalers": "HorizontalPodAutoscaler",
    "service": "Service", "services": "Service", "svc": "Service",
    "ingress": "Ingress", "ingresses": "Ingress",
    "configmap": "ConfigMap", "configmaps": "ConfigMap", "cm": "ConfigMap",
    "secret": "Secret", "secrets": "Secret",
    "job": "Job", "jobs": "Job",
    "cronjob": "CronJob", "cronjobs": "CronJob",
    "pvc": "PersistentVolumeClaim",
    "persistentvolumeclaim": "PersistentVolumeClaim",
    "persistentvolumeclaims": "PersistentVolumeClaim",
    "node": "Node", "nodes": "Node",
    "namespace": "Namespace", "namespaces": "Namespace",
}


def normalize_kind(resource_type: str) -> str:
    return _KIND_MAP.get(resource_type.lower(), resource_type)


class KubectlServiceProtocol(Protocol):
    def run(self, args: list[str]) -> str: ...
    def run_interactive(self, args: list[str]) -> int: ...
    def current_namespace(self) -> str: ...
    def normalize_kind(self, resource_type: str) -> str: ...


class KubectlService:
    def run(self, args: list[str]) -> str:
        result = subprocess.run(
            ["kubectl", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def run_interactive(self, args: list[str]) -> int:
        result = subprocess.run(["kubectl", *args])
        return result.returncode

    def current_namespace(self) -> str:
        result = subprocess.run(
            ["kubectl", "config", "view", "--minify", "-o", "jsonpath={..namespace}"],
            capture_output=True,
            text=True,
            check=True,
        )
        ns = result.stdout.strip()
        return ns if ns else "default"

    def normalize_kind(self, resource_type: str) -> str:
        return normalize_kind(resource_type)
