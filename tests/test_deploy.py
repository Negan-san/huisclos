"""Tests de préparation au déploiement sur Streamlit Community Cloud.

Vérifient des fichiers et le code de l'interface, sans réseau : dépendances légères et
épinglées, configuration sans télémétrie, moteur partagé entre sessions, aucune donnée de
l'utilisateur mise en cache ni écrite sur le disque du serveur.
"""

import ast
import re
import tomllib
from pathlib import Path

import pytest

from app.engine import prepare_engine
from app.i18n import EN
from huisclos.config import PRESETS
from huisclos.detection.pipeline import analyzer_for

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
APP_FILES = [ROOT / "streamlit_app.py", *sorted((ROOT / "app").rglob("*.py"))]
# Une ligne épinglée : "nom==version" ou "nom @ https://.../fichier.whl".
PINNED = re.compile(
    r"^[A-Za-z0-9_.\-\[\]]+(==[0-9][^\s;]*| @ https://\S+\.whl(?:#sha256=[0-9a-f]{64})?)$"
)
DISK_WRITE_METHODS = {"write_text", "write_bytes", "mkdir", "makedirs", "touch", "save"}
# Mode d'ouverture en écriture, pour open(chemin, "w") comme pour Path.open("a").
WRITE_MODE = re.compile(r"^[rbt]*[wax+][rwabxt+]*$")


def requirement_lines() -> list[str]:
    """Renvoie les lignes utiles de requirements.txt, sans blancs ni commentaires."""
    lines = REQUIREMENTS.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def app_calls() -> list[tuple[Path, ast.Call]]:
    """Renvoie tous les appels de fonction du code de l'interface, avec leur fichier."""
    calls = []
    for path in APP_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls.extend((path, node) for node in ast.walk(tree) if isinstance(node, ast.Call))
    return calls


def string_arguments(call: ast.Call) -> list[str]:
    """Renvoie les chaînes littérales passées à un appel, en position ou par mot-clé."""
    values = [*call.args, *(keyword.value for keyword in call.keywords)]
    return [v.value for v in values if isinstance(v, ast.Constant) and isinstance(v.value, str)]


def call_name(call: ast.Call) -> str:
    """Renvoie le nom final de la fonction appelée (open, write_text, cache_data)."""
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return ""


def test_requirements_exclude_heavy_libraries() -> None:
    names = [re.split(r"[=@ \[]", line, maxsplit=1)[0].lower() for line in requirement_lines()]
    assert names
    assert "torch" not in names
    assert "transformers" not in names
    assert "gliner" not in names


def test_every_requirement_is_pinned() -> None:
    unpinned = [line for line in requirement_lines() if not PINNED.match(line)]
    assert unpinned == []


def test_pinned_pattern_rejects_loose_lines() -> None:
    for line in ("streamlit", "streamlit>=1.0", "spacy~=3.8", "model @ https://x/y.tar.gz"):
        assert not PINNED.match(line)


def test_pinned_model_hash_must_be_complete() -> None:
    """Un wheel avec empreinte complète reste épinglé, une empreinte tronquée est refusée."""
    wheel = "en_core_web_sm @ https://example.org/en_core_web_sm-3.8.0.whl"
    assert PINNED.fullmatch(wheel + "#sha256=" + "a" * 64)
    assert not PINNED.fullmatch(wheel + "#sha256=abc")


def test_write_mode_pattern() -> None:
    assert all(WRITE_MODE.match(mode) for mode in ("w", "wb", "a", "x", "r+", "w+b"))
    assert not any(WRITE_MODE.match(mode) for mode in ("r", "rb", "data.txt", "utf-8"))


def test_entry_point_exists() -> None:
    assert (ROOT / "streamlit_app.py").is_file()


def test_usage_statistics_are_disabled() -> None:
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert config["browser"]["gatherUsageStats"] is False


def test_engine_is_built_once_and_shared_with_detect() -> None:
    config = PRESETS["hybrid"]
    first = prepare_engine(config)
    assert prepare_engine(config) is first
    assert analyzer_for(config) is first


def test_user_data_is_never_cached_between_sessions() -> None:
    assert [path.name for path, call in app_calls() if call_name(call) == "cache_data"] == []
    resources = [path.name for path, call in app_calls() if call_name(call) == "cache_resource"]
    assert resources == ["engine.py"]


def test_interface_never_writes_to_the_server_disk() -> None:
    writes = []
    for path, call in app_calls():
        name = call_name(call)
        if name in DISK_WRITE_METHODS:
            writes.append(f"{path.name}:{call.lineno}")
        elif name == "open" and any(WRITE_MODE.match(value) for value in string_arguments(call)):
            writes.append(f"{path.name}:{call.lineno}")
    assert writes == []


@pytest.mark.parametrize("name", ["README.md", "docs/USER_GUIDE.md", "docs/DEPLOYMENT.md"])
def test_documentation_internal_links_exist(name: str) -> None:
    """Vérifie les liens locaux et les captures des trois documents de démarrage."""
    document = ROOT / name
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8"))
    local_links = [link for link in links if "://" not in link and not link.startswith("#")]
    assert all((document.parent / link.split("#")[0]).is_file() for link in local_links)


def test_readme_results_match_saved_summary() -> None:
    """Compare les lignes de résultats publiées aux mesures enregistrées, sans les recalculer."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = (ROOT / "results/summary.md").read_text(encoding="utf-8")
    rows = [line for line in readme.splitlines() if line.startswith(("| dev |", "| test |"))]
    assert rows
    assert all(row in summary.splitlines() for row in rows)


def test_user_guide_workflow_actions_exist_in_english_interface() -> None:
    """Relie les boutons des instructions de travail aux textes anglais de l'interface."""
    guide = (ROOT / "docs/USER_GUIDE.md").read_text(encoding="utf-8")
    workflow = guide.split("## 3. ", 1)[1].split("## 7. ", 1)[0]
    workflow = re.sub(r"\s+", " ", workflow)
    labels = re.findall(r"(?:click|confirmation\s*\()\s*\*\*([^*]+)\*\*", workflow, re.I)
    assert labels
    assert all(label in EN.values() for label in labels)
