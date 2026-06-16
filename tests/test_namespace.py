from unittest.mock import MagicMock, call

from kx.commands.namespace import NamespaceCommand, _parse_all_output
from kx.kinds import Kind

_SAMPLE_OUTPUT = """\
NAME                              READY   STATUS    RESTARTS   AGE
pod/nginx-6b9fb4b4c4-abc          1/1     Running   0          1d
pod/nginx-6b9fb4b4c4-def          1/1     Running   0          1d

NAME                     TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
service/kubernetes       ClusterIP   10.96.0.1     <none>        443/TCP   7d

NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/nginx     1/1     1            1           1d

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/nginx-6b9fb4b4c4     1         1         1       1d
"""


def _make_command(get_all_output=_SAMPLE_OUTPUT):
    kubectl = MagicMock()
    kubectl.run.side_effect = ["", get_all_output]
    state = MagicMock()
    return NamespaceCommand(kubectl=kubectl, state=state), state, kubectl


class TestNamespaceCommandKubectlCalls:
    def test_sets_context_namespace(self):
        cmd, _, kubectl = _make_command()
        cmd.execute("my-ns")
        assert (
            call(["config", "set-context", "--current", "--namespace=my-ns"])
            in kubectl.run.call_args_list
        )

    def test_fetches_all_resources(self):
        cmd, _, kubectl = _make_command()
        cmd.execute("my-ns")
        assert call(["get", "all", "-n", "my-ns"]) in kubectl.run.call_args_list

    def test_context_call_before_get_all(self):
        cmd, _, kubectl = _make_command()
        cmd.execute("my-ns")
        assert kubectl.run.call_args_list[0] == call(
            ["config", "set-context", "--current", "--namespace=my-ns"]
        )
        assert kubectl.run.call_args_list[1] == call(["get", "all", "-n", "my-ns"])


class TestNamespaceCommandStateSave:
    def test_saves_state_with_correct_namespace(self):
        cmd, state, _ = _make_command()
        cmd.execute("my-ns")
        saved = state.save.call_args[0][0]
        assert saved.namespace == "my-ns"

    def test_saves_parsed_resources(self):
        cmd, state, _ = _make_command()
        cmd.execute("my-ns")
        saved = state.save.call_args[0][0]
        assert "nginx-6b9fb4b4c4-abc" in saved.resources
        assert saved.resources["nginx-6b9fb4b4c4-abc"] == Kind.Pod
        assert "kubernetes" in saved.resources
        assert saved.resources["kubernetes"] == Kind.Service
        assert "nginx" in saved.resources
        assert saved.resources["nginx"] == Kind.Deployment

    def test_empty_output_saves_empty_resources(self):
        cmd, state, _ = _make_command(
            get_all_output="No resources found in my-ns namespace."
        )
        cmd.execute("my-ns")
        saved = state.save.call_args[0][0]
        assert saved.resources == {}

    def test_raises_on_kubectl_error(self):
        kubectl = MagicMock()
        kubectl.run.side_effect = RuntimeError("kubectl failed")
        state = MagicMock()
        cmd = NamespaceCommand(kubectl=kubectl, state=state)
        try:
            cmd.execute("my-ns")
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass


class TestParseAllOutput:
    def test_single_pod_section(self):
        output = "NAME                   READY   STATUS    RESTARTS   AGE\npod/nginx-abc          1/1     Running   0          1d"
        result = _parse_all_output(output)
        assert result == {"nginx-abc": Kind.Pod}

    def test_strips_type_prefix_from_name(self):
        output = "NAME                   READY   STATUS    RESTARTS   AGE\npod/nginx-abc          1/1     Running   0          1d"
        result = _parse_all_output(output)
        assert "nginx-abc" in result
        assert "pod/nginx-abc" not in result

    def test_deployment_apps_prefix(self):
        output = "NAME                    READY   UP-TO-DATE   AVAILABLE   AGE\ndeployment.apps/nginx   1/1     1            1           1d"
        result = _parse_all_output(output)
        assert result == {"nginx": Kind.Deployment}

    def test_replicaset_apps_prefix(self):
        output = "NAME                           DESIRED   CURRENT   READY   AGE\nreplicaset.apps/nginx-abc123   1         1         1       1d"
        result = _parse_all_output(output)
        assert result == {"nginx-abc123": Kind.ReplicaSet}

    def test_statefulset_apps_prefix(self):
        output = (
            "NAME                    READY   AGE\nstatefulset.apps/pg     1/1     2d"
        )
        result = _parse_all_output(output)
        assert result == {"pg": Kind.StatefulSet}

    def test_service_prefix(self):
        output = "NAME                TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE\nservice/kubernetes   ClusterIP   10.96.0.1     <none>        443/TCP   7d"
        result = _parse_all_output(output)
        assert result == {"kubernetes": Kind.Service}

    def test_multiple_sections(self):
        result = _parse_all_output(_SAMPLE_OUTPUT)
        assert "nginx-6b9fb4b4c4-abc" in result
        assert "nginx-6b9fb4b4c4-def" in result
        assert "kubernetes" in result
        assert "nginx" in result
        assert "nginx-6b9fb4b4c4" in result

    def test_insertion_order_preserved(self):
        result = _parse_all_output(_SAMPLE_OUTPUT)
        keys = list(result.keys())
        assert keys.index("nginx-6b9fb4b4c4-abc") < keys.index("kubernetes")
        assert keys.index("kubernetes") < keys.index("nginx")

    def test_section_without_name_header_skipped(self):
        output = "REASON   MESSAGE\nFailed   something went wrong"
        result = _parse_all_output(output)
        assert result == {}

    def test_empty_output(self):
        assert _parse_all_output("") == {}

    def test_no_resources_message(self):
        assert _parse_all_output("No resources found in my-ns namespace.") == {}

    def test_rows_without_slash_skipped(self):
        output = "NAME        READY\nnginx       1/1"
        result = _parse_all_output(output)
        assert result == {}
