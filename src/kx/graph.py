from kubernetes import client
from rich.tree import Tree

from kx.k8s import load_config


def build_tree(kind: str, name: str, namespace: str) -> Tree:
    load_config()
    root = Tree(f"[bold]{kind}/{name}[/bold]")

    apps = client.AppsV1Api()
    core = client.CoreV1Api()
    batch = client.BatchV1Api()

    pods = core.list_namespaced_pod(namespace).items

    if kind == "Deployment":
        _tree_deployment(name, namespace, root, apps, pods)
    elif kind == "ReplicaSet":
        _tree_replica_set(name, namespace, root, apps, pods)
    elif kind == "StatefulSet":
        _tree_stateful_set(name, namespace, root, apps, pods)
    elif kind == "DaemonSet":
        _tree_daemon_set(name, namespace, root, apps, pods)
    elif kind == "CronJob":
        _tree_cron_job(name, namespace, root, batch, pods)
    elif kind == "Pod":
        pod = core.read_namespaced_pod(name, namespace)
        _add_containers(pod, root)
    else:
        root.add(f"[dim](no ownership graph for {kind})[/dim]")

    return root


def _tree_deployment(name, namespace, node, apps, pods):
    deploy = apps.read_namespaced_deployment(name, namespace)
    uid = deploy.metadata.uid
    replica_sets = [
        rs for rs in apps.list_namespaced_replica_set(namespace).items
        if _owned_by(rs, uid)
    ]
    for rs in replica_sets:
        rs_node = node.add(f"[green]rs/{rs.metadata.name}[/green]")
        _add_pods_for_owner(rs.metadata.uid, pods, rs_node)


def _tree_replica_set(name, namespace, node, apps, pods):
    rs = apps.read_namespaced_replica_set(name, namespace)
    _add_pods_for_owner(rs.metadata.uid, pods, node)


def _tree_stateful_set(name, namespace, node, apps, pods):
    sts = apps.read_namespaced_stateful_set(name, namespace)
    _add_pods_for_owner(sts.metadata.uid, pods, node)


def _tree_daemon_set(name, namespace, node, apps, pods):
    ds = apps.read_namespaced_daemon_set(name, namespace)
    _add_pods_for_owner(ds.metadata.uid, pods, node)


def _tree_cron_job(name, namespace, node, batch, pods):
    cj = batch.read_namespaced_cron_job(name, namespace)
    uid = cj.metadata.uid
    jobs = [
        j for j in batch.list_namespaced_job(namespace).items
        if _owned_by(j, uid)
    ]
    for job in jobs:
        job_node = node.add(f"[green]job/{job.metadata.name}[/green]")
        _add_pods_for_owner(job.metadata.uid, pods, job_node)


def _add_pods_for_owner(owner_uid, pods, parent_node):
    owned = [p for p in pods if _owned_by(p, owner_uid)]
    for pod in owned:
        pod_node = parent_node.add(f"[blue]pod/{pod.metadata.name}[/blue]")
        _add_containers(pod, pod_node)


def _add_containers(pod, parent_node):
    for container in pod.spec.containers:
        parent_node.add(f"[cyan]container: {container.name}[/cyan]")


def _owned_by(resource, uid: str) -> bool:
    refs = resource.metadata.owner_references or []
    return any(ref.uid == uid for ref in refs)
