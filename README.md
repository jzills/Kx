# kx

`kx` is a kubectl wrapper that adds index-based resource selection. Run `kx get <resource>` once, then reference any result by number instead of typing full resource names.

## Install

```bash
pip install kx-cli
```

## Usage

### List resources

```
kx get <resource> [-n <namespace>]
```

Fetches resources and assigns index numbers. Omitting `-n` uses the current context namespace.

```
$ kx get pods
X  NAME                          READY  STATUS   RESTARTS  AGE
1  api-7d9f4b8c6-xkp2q           1/1    Running  0         2d
2  worker-6c8b5f7d9-mnt4r        1/1    Running  3         5h
3  postgres-0                    1/1    Running  0         12d
```

All subsequent commands reference resources by their `X` index from the last `kx get`.

### Commands

| Command | Description |
|---|---|
| `kx get <resource> [-n ns]` | List resources with index numbers |
| `kx describe <index> [--view events]` | Show `kubectl describe` output; `--view events` filters to events only |
| `kx events <index>` | Show Kubernetes events for the resource |
| `kx logs <index>` | Stream logs for a pod |
| `kx yaml <index>` | Print the raw YAML manifest |
| `kx exec <index> [cmd]` | Open an interactive shell in a pod (bash → sh fallback); pass a custom command with `cmd` |
| `kx edit <index>` | Open the resource in your editor via `kubectl edit` |
| `kx delete <index> [-y]` | Delete the resource (prompts for confirmation; `-y` skips it) |
| `kx tree <index>` | Show the ownership graph for a resource |
| `kx port-forward <index> <port>` | Forward a local port to a resource (supports Pod, Deployment, ReplicaSet, StatefulSet, DaemonSet, Service) |

### Example workflow

```bash
# list deployments, pick index 2
kx get deployments
kx describe 2

# check events on that deployment
kx events 2

# drill into a pod
kx get pods
kx logs 1
kx exec 1            # opens bash/sh
kx exec 1 -- env     # run a specific command

# forward local port 8080 to port 80 on a service
kx get services
kx port-forward 2 8080:80

# clean up
kx delete 3
```

## State

`kx` saves the last `get` result to `~/.kx_state.json`. Index-based commands read from this file, so switching namespaces or resource types requires a new `kx get`.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the CLI directly:

```bash
python -m kx.main --help
```
