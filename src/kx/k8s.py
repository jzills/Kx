from kubernetes import config


def load_config():
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()
