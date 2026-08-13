from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT_DIR / "images"
STATE_DIR = ROOT_DIR / "state"


@dataclass
class PluginConfig:
    name: str
    source_type: str
    source_repository: str
    version_pattern: str


@dataclass
class ImageConfig:
    name: str
    source_type: str
    source_repository: str

    target_registry: str
    target_repository: str

    version_pattern: str
    minimum_major: int | None

    dockerfile: Path
    tags: list[str]

    plugins: list[PluginConfig]


def load_configs() -> list[ImageConfig]:
    configs = []

    for path in sorted(IMAGES_DIR.glob("*/image.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)

        source = data["source"]
        target = data["target"]
        versions = data["versions"]
        build = data["build"]

        plugins = []

        for plugin in data.get("plugins", []):
            plugin_source = plugin["source"]
            plugin_version = plugin["version"]

            plugins.append(
                PluginConfig(
                    name=plugin["name"],
                    source_type=plugin_source["type"],
                    source_repository=plugin_source["repository"],
                    version_pattern=plugin_version["pattern"],
                )
            )

        configs.append(
            ImageConfig(
                name=data["name"],
                source_type=source["type"],
                source_repository=source["repository"],
                target_registry=target["registry"],
                target_repository=target["repository"],
                version_pattern=versions["pattern"],
                minimum_major=versions.get("minimum_major"),
                dockerfile=path.parent / build["dockerfile"],
                tags=data.get("tags", []),
                plugins=plugins,
            )
        )

    return configs


def version_matches(
    pattern: str,
    version: str,
    minimum_major: int | None = None,
) -> bool:
    if not re.match(pattern, version):
        return False

    if minimum_major is not None:
        try:
            major = int(version.split(".")[0])
        except ValueError:
            return False

        if major < minimum_major:
            return False

    return True


def expand_template(value: str, version: str) -> str:
    return value.replace("{version}", version)
