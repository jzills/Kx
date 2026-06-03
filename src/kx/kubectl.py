import subprocess
from typing import Protocol

from kx.kinds import Kind

_KIND_MAP: dict[str, Kind] = {
    "po": Kind.Pod, "pod": Kind.Pod, "pods": Kind.Pod,
    "deployment": Kind.Deployment, "deployments": Kind.Deployment, "deploy": Kind.Deployment,
    "replicaset": Kind.ReplicaSet, "replicasets": Kind.ReplicaSet, "rs": Kind.ReplicaSet,
    "statefulset": Kind.StatefulSet, "statefulsets": Kind.StatefulSet, "sts": Kind.StatefulSet,
    "daemonset": Kind.DaemonSet, "daemonsets": Kind.DaemonSet, "ds": Kind.DaemonSet,
    "hpa": Kind.HorizontalPodAutoscaler,
    "horizontalpodautoscaler": Kind.HorizontalPodAutoscaler,
    "horizontalpodautoscalers": Kind.HorizontalPodAutoscaler,
    "service": Kind.Service, "services": Kind.Service, "svc": Kind.Service,
    "ingress": Kind.Ingress, "ingresses": Kind.Ingress,
    "configmap": Kind.ConfigMap, "configmaps": Kind.ConfigMap, "cm": Kind.ConfigMap,
    "secret": Kind.Secret, "secrets": Kind.Secret,
    "job": Kind.Job, "jobs": Kind.Job,
    "cronjob": Kind.CronJob, "cronjobs": Kind.CronJob,
    "pvc": Kind.PersistentVolumeClaim,
    "persistentvolumeclaim": Kind.PersistentVolumeClaim,
    "persistentvolumeclaims": Kind.PersistentVolumeClaim,
    "node": Kind.Node, "nodes": Kind.Node,
    "namespace": Kind.Namespace, "namespaces": Kind.Namespace,
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
