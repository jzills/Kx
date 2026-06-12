from kubernetes import client
from rich.tree import Tree

from kx.k8s import load_config
from kx.kinds import Kind

_COLOR_ROOT = "#3fb950"
_COLOR_MID = "#3fb950"
_COLOR_POD = "#e6edf3"
_COLOR_DIM = "#7d8590"


def build_tree(kind: str, name: str, namespace: str) -> Tree:
    load_config()
    root = Tree(f"[bold {_COLOR_ROOT}]{kind}/{name}[/bold {_COLOR_ROOT}]")

    apps = client.AppsV1Api()
    core = client.CoreV1Api()
    batch = client.BatchV1Api()

    pods = core.list_namespaced_pod(namespace).items

    match kind:
        case Kind.Deployment:
            _tree_deployment(name, namespace, root, apps, pods)
        case Kind.ReplicaSet:
            _tree_replica_set(name, namespace, root, apps, pods)
        case Kind.StatefulSet:
            _tree_stateful_set(name, namespace, root, apps, pods)
        case Kind.DaemonSet:
            _tree_daemon_set(name, namespace, root, apps, pods)
        case Kind.CronJob:
            _tree_cron_job(name, namespace, root, batch, pods)
        case Kind.Service:
            _tree_service(name, namespace, root, core)
        case Kind.Pod:
            pod = core.read_namespaced_pod(name, namespace)
            _add_containers(pod, root)
        case _:
            root.add(f"[dim](no ownership graph for {kind})[/dim]")

    return root


def _tree_deployment(name, namespace, node, apps, pods):
    deploy = apps.read_namespaced_deployment(name, namespace)
    uid = deploy.metadata.uid
    replica_sets = [
        rs
        for rs in apps.list_namespaced_replica_set(namespace).items
        if _owned_by(rs, uid)
    ]
    for rs in replica_sets:
        rs_node = node.add(f"[{_COLOR_MID}]rs/{rs.metadata.name}[/{_COLOR_MID}]")
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
        job for job in batch.list_namespaced_job(namespace).items if _owned_by(job, uid)
    ]
    for job in jobs:
        job_node = node.add(f"[{_COLOR_MID}]job/{job.metadata.name}[/{_COLOR_MID}]")
        _add_pods_for_owner(job.metadata.uid, pods, job_node)


def _tree_service(name, namespace, node, core):
    svc = core.read_namespaced_service(name, namespace)
    selector = svc.spec.selector
    if not selector:
        node.add(f"[{_COLOR_DIM}](no selector)[/{_COLOR_DIM}]")
        return
    label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
    pods = core.list_namespaced_pod(namespace, label_selector=label_selector).items
    if not pods:
        node.add(f"[{_COLOR_DIM}](no matching pods)[/{_COLOR_DIM}]")
        return
    for pod in pods:
        pod_node = node.add(f"[{_COLOR_POD}]pod/{pod.metadata.name}[/{_COLOR_POD}]")
        _add_containers(pod, pod_node)


def _add_pods_for_owner(owner_uid, pods, parent_node):
    owned = [pod for pod in pods if _owned_by(pod, owner_uid)]
    for pod in owned:
        pod_node = parent_node.add(
            f"[{_COLOR_POD}]pod/{pod.metadata.name}[/{_COLOR_POD}]"
        )
        _add_containers(pod, pod_node)


def _add_containers(pod, parent_node):
    for container in pod.spec.containers:
        parent_node.add(f"[{_COLOR_DIM}]container: {container.name}[/{_COLOR_DIM}]")


def _owned_by(resource, uid: str) -> bool:
    refs = resource.metadata.owner_references or []
    return any(ref.uid == uid for ref in refs)


def build_indexed_tree(
    kind: str, name: str, namespace: str
) -> tuple[Tree, list[tuple[str, str]]]:
    load_config()
    resources: list[tuple[str, str]] = [(name, kind)]
    root = Tree(
        f"[{_COLOR_DIM}]1[/{_COLOR_DIM}] [bold {_COLOR_ROOT}]{kind}/{name}[/bold {_COLOR_ROOT}]"
    )

    apps = client.AppsV1Api()
    core = client.CoreV1Api()
    batch = client.BatchV1Api()

    pods = core.list_namespaced_pod(namespace).items

    match kind:
        case Kind.Deployment:
            _indexed_tree_deployment(name, namespace, root, apps, pods, resources)
        case Kind.ReplicaSet:
            _indexed_tree_replica_set(name, namespace, root, apps, pods, resources)
        case Kind.StatefulSet:
            _indexed_tree_stateful_set(name, namespace, root, apps, pods, resources)
        case Kind.DaemonSet:
            _indexed_tree_daemon_set(name, namespace, root, apps, pods, resources)
        case Kind.CronJob:
            _indexed_tree_cron_job(name, namespace, root, batch, pods, resources)
        case Kind.Service:
            _indexed_tree_service(name, namespace, root, core, resources)
        case Kind.Pod:
            pod = core.read_namespaced_pod(name, namespace)
            _add_containers(pod, root)
        case _:
            root.add(f"[dim](no ownership graph for {kind})[/dim]")

    return root, resources


def _indexed_tree_deployment(name, namespace, node, apps, pods, resources):
    deploy = apps.read_namespaced_deployment(name, namespace)
    uid = deploy.metadata.uid
    replica_sets = [
        rs
        for rs in apps.list_namespaced_replica_set(namespace).items
        if _owned_by(rs, uid)
    ]
    for rs in replica_sets:
        idx = len(resources) + 1
        rs_node = node.add(
            f"[{_COLOR_DIM}]{idx}[/{_COLOR_DIM}] [{_COLOR_MID}]rs/{rs.metadata.name}[/{_COLOR_MID}]"
        )
        resources.append((rs.metadata.name, Kind.ReplicaSet))
        _indexed_add_pods_for_owner(rs.metadata.uid, pods, rs_node, resources)


def _indexed_tree_replica_set(name, namespace, node, apps, pods, resources):
    rs = apps.read_namespaced_replica_set(name, namespace)
    _indexed_add_pods_for_owner(rs.metadata.uid, pods, node, resources)


def _indexed_tree_stateful_set(name, namespace, node, apps, pods, resources):
    sts = apps.read_namespaced_stateful_set(name, namespace)
    _indexed_add_pods_for_owner(sts.metadata.uid, pods, node, resources)


def _indexed_tree_daemon_set(name, namespace, node, apps, pods, resources):
    ds = apps.read_namespaced_daemon_set(name, namespace)
    _indexed_add_pods_for_owner(ds.metadata.uid, pods, node, resources)


def _indexed_tree_cron_job(name, namespace, node, batch, pods, resources):
    cj = batch.read_namespaced_cron_job(name, namespace)
    uid = cj.metadata.uid
    jobs = [
        job for job in batch.list_namespaced_job(namespace).items if _owned_by(job, uid)
    ]
    for job in jobs:
        idx = len(resources) + 1
        job_node = node.add(
            f"[{_COLOR_DIM}]{idx}[/{_COLOR_DIM}] [{_COLOR_MID}]job/{job.metadata.name}[/{_COLOR_MID}]"
        )
        resources.append((job.metadata.name, Kind.Job))
        _indexed_add_pods_for_owner(job.metadata.uid, pods, job_node, resources)


def _indexed_tree_service(name, namespace, node, core, resources):
    svc = core.read_namespaced_service(name, namespace)
    selector = svc.spec.selector
    if not selector:
        node.add(f"[{_COLOR_DIM}](no selector)[/{_COLOR_DIM}]")
        return
    label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
    pods = core.list_namespaced_pod(namespace, label_selector=label_selector).items
    if not pods:
        node.add(f"[{_COLOR_DIM}](no matching pods)[/{_COLOR_DIM}]")
        return
    for pod in pods:
        idx = len(resources) + 1
        pod_node = node.add(
            f"[{_COLOR_DIM}]{idx}[/{_COLOR_DIM}] [{_COLOR_POD}]pod/{pod.metadata.name}[/{_COLOR_POD}]"
        )
        resources.append((pod.metadata.name, Kind.Pod))
        _add_containers(pod, pod_node)


def _indexed_add_pods_for_owner(owner_uid, pods, parent_node, resources):
    owned = [pod for pod in pods if _owned_by(pod, owner_uid)]
    for pod in owned:
        idx = len(resources) + 1
        pod_node = parent_node.add(
            f"[{_COLOR_DIM}]{idx}[/{_COLOR_DIM}] [{_COLOR_POD}]pod/{pod.metadata.name}[/{_COLOR_POD}]"
        )
        resources.append((pod.metadata.name, Kind.Pod))
        _add_containers(pod, pod_node)
