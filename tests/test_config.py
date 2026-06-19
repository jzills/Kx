import pytest
from unittest.mock import patch
from kx.config import load_config


def _patch_config_file(path):
    return patch("kx.config._CONFIG_FILE", path)


def _clear_env(monkeypatch):
    monkeypatch.delenv("KX_MAX_HISTORY", raising=False)
    monkeypatch.delenv("KX_SHELLS", raising=False)


class TestConfigDefaults:
    def test_defaults_when_no_file_and_no_env(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        with _patch_config_file(tmp_path / "config.toml"):
            config = load_config()
        assert config.max_history == 10
        assert config.shells == ("bash", "sh")


class TestConfigFile:
    def test_max_history_from_file(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        config_file = tmp_path / "config.toml"
        config_file.write_text("max_history = 5\n")
        with _patch_config_file(config_file):
            config = load_config()
        assert config.max_history == 5

    def test_shells_from_file(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        config_file = tmp_path / "config.toml"
        config_file.write_text('shells = ["zsh", "bash", "sh"]\n')
        with _patch_config_file(config_file):
            config = load_config()
        assert config.shells == ("zsh", "bash", "sh")

    def test_unknown_keys_ignored(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        config_file = tmp_path / "config.toml"
        config_file.write_text("max_history = 3\nunknown_key = true\n")
        with _patch_config_file(config_file):
            config = load_config()
        assert config.max_history == 3

    def test_malformed_toml_raises_system_exit(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        config_file = tmp_path / "config.toml"
        config_file.write_text("max_history = [not valid\n")
        with _patch_config_file(config_file):
            with pytest.raises(SystemExit, match="error reading"):
                load_config()


class TestEnvOverrides:
    def test_env_max_history_overrides_default(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("KX_MAX_HISTORY", "20")
        with _patch_config_file(tmp_path / "config.toml"):
            config = load_config()
        assert config.max_history == 20

    def test_env_shells_overrides_default(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("KX_SHELLS", "zsh,bash,sh")
        with _patch_config_file(tmp_path / "config.toml"):
            config = load_config()
        assert config.shells == ("zsh", "bash", "sh")

    def test_env_overrides_file(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        config_file = tmp_path / "config.toml"
        config_file.write_text("max_history = 5\n")
        monkeypatch.setenv("KX_MAX_HISTORY", "15")
        with _patch_config_file(config_file):
            config = load_config()
        assert config.max_history == 15

    def test_invalid_max_history_raises_system_exit(self, tmp_path, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("KX_MAX_HISTORY", "notanumber")
        with _patch_config_file(tmp_path / "config.toml"):
            with pytest.raises(SystemExit, match="KX_MAX_HISTORY must be an integer"):
                load_config()
