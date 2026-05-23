from kubernetes import client, config

def load_k8s():
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()