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
