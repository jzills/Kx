<div align="center">
  <img src="https://raw.githubusercontent.com/jzills/kx/main/assets/banner.svg" alt="kx — kubectl, indexed." width="800"/>
</div>

<br>

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/kx-cli?style=flat-square&color=3fb950&labelColor=21262d)](https://pypi.org/project/kx-cli/)
[![Python](https://img.shields.io/pypi/pyversions/kx-cli?style=flat-square&color=3fb950&labelColor=21262d)](https://pypi.org/project/kx-cli/)
[![License](https://img.shields.io/github/license/jzills/kx?style=flat-square&color=3fb950&labelColor=21262d)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/jzills/kx/pr.yml?style=flat-square&color=3fb950&labelColor=21262d&label=CI)](https://github.com/jzills/kx/actions/workflows/pr.yml)

</div>

`kx` is a kubectl wrapper that adds index-based resource selection. Run `kx get <resource>` once, then reference any result by number instead of typing full resource names.

<div align="center">
  <img src="https://raw.githubusercontent.com/jzills/kx/main/demo/demo.gif" alt="kx demo" width="800"/>
</div>

## Install

```bash
pip install kx-cli
```

## Usage

### List resources

```
kx get <resource> [--match|-m <substring>] [kubectl flags...]
```

Fetches resources and assigns index numbers. Any extra flags (e.g. `-n <namespace>`, `-A`) are passed through to kubectl. Use `--match`/`-m` to filter results by name (substring, case-insensitive).

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
| `kx get <resource> [--match\|-m <str>] [kubectl flags...]` | List resources with index numbers; optionally filter by name substring |
| `kx describe <index> [kubectl flags...]` | Show `kubectl describe` output for an indexed resource |
| `kx events <index>` | Show Kubernetes events for the resource |
| `kx labels <index>` | Show labels for an indexed resource |
| `kx logs <index> [kubectl flags...]` | Stream logs; aggregates across pods for Deployments, StatefulSets, DaemonSets, and Services |
| `kx yaml <index>` | Print the raw YAML manifest |
| `kx exec <index> [cmd] [kubectl flags...]` | Open an interactive shell in a pod (bash → sh fallback); pass a custom command with `cmd` |
| `kx edit <index> [kubectl flags...]` | Open the resource in your editor via `kubectl edit` |
| `kx delete <index> [-y]` | Delete the resource (prompts for confirmation; `-y` skips it) |
| `kx tree <index> [--index\|-i]` | Show the ownership graph for a resource; `--index` assigns indexes to tree nodes |
| `kx port-forward <index> <port> [kubectl flags...]` | Forward a local port to a resource (supports Pod, Deployment, ReplicaSet, StatefulSet, DaemonSet, Service) |
| `kx state` | Show the current state (namespace and indexed resources from the last `kx get`) |

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
