"""Vérifie les frontières de distribution et les choix d'installation du kit.

Les commandes d'installation sont simulées ; aucun paquet ni poids n'est téléchargé.
Les archives de contrôle proviennent d'un dépôt Git temporaire entièrement fictif.
"""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts import build_toolkit as builder
from scripts import toolkit_enhanced as enhanced
from scripts import toolkit_launcher as launcher


@pytest.fixture
def installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "kit avec espaces"
    root.mkdir()
    (root / "requirements.txt").write_text("streamlit==1.66.1\n", encoding="utf-8")
    monkeypatch.setattr(launcher, "ROOT", root)
    monkeypatch.setattr(launcher, "ENVIRONMENT", root / ".venv-toolkit")
    monkeypatch.setattr(launcher, "MARKER", root / ".venv-toolkit/huisclos-install.json")
    return root


@pytest.fixture
def commands(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    recorded = []

    def record(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(launcher, "run", record)
    return recorded


def make_environment() -> None:
    launcher.environment_python().parent.mkdir(parents=True)
    launcher.environment_python().touch()


def test_current_installation_never_runs_pip_install(
    installation: Path, commands: list[list[str]]
) -> None:
    make_environment()
    launcher.MARKER.write_text(json.dumps(launcher.installation_identity()), encoding="utf-8")
    launcher.prepare_installation()
    assert len(commands) == 2
    assert all("install" not in command for command in commands)


def test_changed_requirements_require_new_receipt(
    installation: Path, commands: list[list[str]]
) -> None:
    make_environment()
    launcher.MARKER.write_text(json.dumps(launcher.installation_identity()), encoding="utf-8")
    (installation / "requirements.txt").write_text("spacy==3.8.18\n", encoding="utf-8")
    assert not launcher.installation_current()
    assert not commands


def test_interrupted_installation_does_not_write_success(
    installation: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_environment()

    def fail(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "install" in command:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(launcher, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        launcher.prepare_installation()
    assert not launcher.MARKER.exists()


def test_installation_receipt_follows_health_check(
    installation: Path, commands: list[list[str]]
) -> None:
    make_environment()
    launcher.prepare_installation()
    assert (
        json.loads(launcher.MARKER.read_text(encoding="utf-8")) == launcher.installation_identity()
    )
    assert any("install" in command for command in commands)
    assert commands[-1][-1] == "--load"


def test_incomplete_environment_is_not_overwritten(
    installation: Path, commands: list[list[str]]
) -> None:
    launcher.ENVIRONMENT.mkdir()
    with pytest.raises(RuntimeError, match="Incomplete"):
        launcher.prepare_installation()
    assert not commands


@pytest.mark.parametrize(
    "answer,expected", [("", "standard"), ("2", "enhanced-fr"), ("3", "enhanced")]
)
def test_first_installation_offers_model_choice(
    installation: Path, monkeypatch: pytest.MonkeyPatch, answer: str, expected: str
) -> None:
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert launcher.choose_models(None) == expected


def test_invalid_choice_is_asked_again(installation: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: True)
    answers = iter(["invalid", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert launcher.choose_models(None) == "enhanced-fr"


def test_noninteractive_default_and_explicit_enhanced(
    installation: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(launcher.sys.stdin, "isatty", lambda: False)
    assert launcher.choose_models(None) == "standard"
    assert launcher.choose_models("enhanced") == "enhanced"


def test_saved_choice_does_not_ask_again(installation: Path, commands: list[list[str]]) -> None:
    make_environment()
    launcher.prepare_models("standard")
    assert launcher.choose_models(None) == "standard"
    assert launcher.choose_models("enhanced-fr") == "enhanced-fr"
    assert not commands


def test_check_does_not_install_or_start_server(
    installation: Path, commands: list[list[str]]
) -> None:
    assert launcher.main(["--check"]) == 0
    assert all("install" not in command and "streamlit" not in command for command in commands)
    assert not launcher.MARKER.exists()


def test_enhanced_diagnostic_is_forwarded(installation: Path, commands: list[list[str]]) -> None:
    assert launcher.main(["--check", "--models", "enhanced-fr"]) == 0
    assert commands[-1][-3:] == ["--models", "enhanced-fr", "--check"]
    assert all("install" not in command for command in commands)


@pytest.mark.parametrize("port", ["0", "65536", "not-a-number"])
def test_invalid_port_prevents_all_actions(
    installation: Path, commands: list[list[str]], port: str
) -> None:
    with pytest.raises(SystemExit):
        launcher.main(["--port", port])
    assert not commands


def test_server_uses_loopback_and_disables_telemetry(installation: Path) -> None:
    command = launcher.streamlit_command(8502)
    assert "--server.address=127.0.0.1" in command
    assert "--server.port=8502" in command
    assert "--browser.gatherUsageStats=false" in command
    assert "--server.headless=false" in command
    assert "--server.showEmailPrompt=false" in command


def test_saved_enhanced_sets_only_local_assets(installation: Path) -> None:
    make_environment()
    choice = launcher.ENVIRONMENT / "huisclos-model-choice.json"
    choice.write_text('{"models": "enhanced-fr"}', encoding="utf-8")
    values = launcher.runtime_environment()
    assert values["HUISCLOS_MODELS_DIR"] == str(launcher.ENVIRONMENT / "model-assets")
    assert values["HF_HUB_OFFLINE"] == "1"
    assert values["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"


@pytest.mark.parametrize(
    "platform,package", [("win32", "torch==2.14.1+cpu"), ("darwin", "torch==2.14.1")]
)
def test_torch_installation_matches_platform(
    monkeypatch: pytest.MonkeyPatch, platform: str, package: str
) -> None:
    monkeypatch.setattr(enhanced.sys, "platform", platform)
    command = enhanced.torch_command()
    assert package in command
    assert ("--index-url" in command) == (platform != "darwin")


def test_failed_enhanced_download_never_confirms_choice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(enhanced, "ASSETS", tmp_path)
    monkeypatch.setattr(enhanced, "CHOICE", tmp_path / "choice.json")
    (tmp_path / "manifest.json").write_text(
        '{"models": {"camembert_ner": {"status": "unavailable"}}}', encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="downloaded or verified"):
        enhanced.verify_models("enhanced-fr")
    assert not enhanced.CHOICE.exists()


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".streamlit/secrets.toml",
        "docs/.env.local",
        "app/client.mapping.json",
        "src/__pycache__/file.pyc",
        "corpus/test.jsonl",
        "corpus/blind_post_g7/fr.jsonl",
        "data/client.txt",
        "results/tmp/message.txt",
        "app/../secrets.toml",
        "/src/config.py",
        "app/.venv/key.txt",
        "app\\private.py",
    ],
)
def test_distribution_refuses_private_and_reserved_paths(name: str) -> None:
    assert not builder.allowed_path(name)


def test_zip_contains_committed_sources_only_and_verifiable_manifest(tmp_path: Path) -> None:
    root = tmp_path / "repo with spaces"
    root.mkdir()
    files = {name: "fixture\n" for name in builder.REQUIRED}
    files.update({"src/huisclos/example.py": "original\n", "docs/.env": "dummy\n"})
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    builder.git_bytes(root, "init", "--quiet")
    builder.git_bytes(root, "add", ".")
    builder.git_bytes(
        root,
        "-c",
        "user.name=Toolkit test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "fixture",
    )
    (root / "src/huisclos/example.py").write_text("uncommitted\n", encoding="utf-8")
    (root / "src/untracked.py").write_text("untracked\n", encoding="utf-8")
    output = builder.build_toolkit(root, tmp_path / "dist")
    original = output.read_bytes()
    assert builder.build_toolkit(root, tmp_path / "dist").read_bytes() == original
    with zipfile.ZipFile(output) as archive:
        prefix = "HuisClos-Toolkit/"
        assert prefix + "docs/.env" not in archive.namelist()
        assert prefix + "src/untracked.py" not in archive.namelist()
        assert archive.read(prefix + "src/huisclos/example.py") == builder.git_bytes(
            root, "show", "HEAD:src/huisclos/example.py"
        )
        manifest = json.loads(archive.read(prefix + "TOOLKIT_MANIFEST.json"))
        for name, digest in manifest["files_sha256"].items():
            assert hashlib.sha256(archive.read(prefix + name)).hexdigest() == digest
        script = archive.getinfo(prefix + "Start-HuisClos-macOS.command")
        assert (script.external_attr >> 16) & 0o111 == 0o111
        assert b"\r" not in archive.read(script)
        assert archive.read(prefix + "Start-HuisClos-Windows.bat") == b"fixture\r\n"
    assert (
        output.with_suffix(".zip.sha256")
        .read_text(encoding="utf-8")
        .startswith(hashlib.sha256(original).hexdigest())
    )


def test_incomplete_source_commit_cannot_produce_kit(tmp_path: Path) -> None:
    builder.git_bytes(tmp_path, "init", "--quiet")
    builder.git_bytes(
        tmp_path,
        "-c",
        "user.name=Toolkit test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "--allow-empty",
        "-m",
        "fixture",
    )
    with pytest.raises(ValueError, match="missing from commit"):
        builder.build_toolkit(tmp_path, tmp_path / "dist")
