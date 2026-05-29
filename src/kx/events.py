from kubernetes import client
from kx.k8s import load_k8s

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
    """Map kubectl shorthand (e.g. 'pods', 'deploy', 'svc') to canonical Kubernetes kind names."""
    return _KIND_MAP.get(resource_type.lower(), resource_type)


def get_events(namespace: str):
    load_k8s()
    v1 = client.CoreV1Api()

    return v1.list_namespaced_event(namespace=namespace).items

def filter_events(events, name: str, kind: str):
    normalized = normalize_kind(kind)
    return [
        e for e in events
        if e.involved_object.name == name
        and e.involved_object.kind == normalized
    ]