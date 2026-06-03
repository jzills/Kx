from enum import StrEnum


class Kind(StrEnum):
    Pod = "Pod"
    Deployment = "Deployment"
    ReplicaSet = "ReplicaSet"
    StatefulSet = "StatefulSet"
    DaemonSet = "DaemonSet"
    CronJob = "CronJob"
    Service = "Service"
    HorizontalPodAutoscaler = "HorizontalPodAutoscaler"
    Ingress = "Ingress"
    ConfigMap = "ConfigMap"
    Secret = "Secret"
    Job = "Job"
    PersistentVolumeClaim = "PersistentVolumeClaim"
    Node = "Node"
    Namespace = "Namespace"


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
