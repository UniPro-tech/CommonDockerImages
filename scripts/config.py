from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml


ROOT_DIR = Path(__file__).resolve().parent.parent

# リポジトリの実際の構成
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

    # version / versions のどちらにも対応
    version_pattern: str
    minimum_major: int | None = None

    dockerfile: Path = field(default_factory=Path)

    # Dockerfile ARG
    build_args: dict[str, str] = field(default_factory=dict)

    tags: list[str] = field(default_factory=list)

    plugins: list[PluginConfig] = field(default_factory=list)


def load_configs() -> list[ImageConfig]:
    configs: list[ImageConfig] = []

    if not IMAGES_DIR.exists():
        raise RuntimeError(f"Images directory does not exist: {IMAGES_DIR}")

    for path in sorted(IMAGES_DIR.glob("*/image.yaml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML: {path}")

        source = data["source"]
        target = data["target"]
        build = data["build"]

        # ------------------------------------------------------------
        # version / versions の両方に対応
        #
        # 通常のイメージ:
        #
        # version:
        #   pattern: ...
        #
        # 複数majorを扱うイメージ:
        #
        # versions:
        #   pattern: ...
        #   minimum_major: 15
        # ------------------------------------------------------------

        version_config = data.get("versions")

        if version_config is None:
            version_config = data.get("version")

        if version_config is None:
            raise ValueError(f"{path}: either 'version' or 'versions' is required")

        if not isinstance(version_config, dict):
            raise ValueError(f"{path}: 'version' must be a mapping")

        version_pattern = version_config["pattern"]

        minimum_major = version_config.get("minimum_major")

        # ------------------------------------------------------------
        # Plugins
        # ------------------------------------------------------------

        plugins: list[PluginConfig] = []

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

        # ------------------------------------------------------------
        # Build args
        # ------------------------------------------------------------

        build_args = dict(build.get("args", {}))

        # ------------------------------------------------------------
        # Config
        # ------------------------------------------------------------

        config = ImageConfig(
            name=data["name"],
            source_type=source["type"],
            source_repository=source["repository"],
            target_registry=target["registry"],
            target_repository=target["repository"],
            version_pattern=version_pattern,
            minimum_major=minimum_major,
            dockerfile=path.parent / build["dockerfile"],
            build_args=build_args,
            tags=data.get("tags", []),
            plugins=plugins,
        )

        configs.append(config)

    return configs


def version_matches(
    pattern: str,
    version: str,
    minimum_major: int | None = None,
) -> bool:
    if not re.fullmatch(pattern, version):
        return False

    if minimum_major is not None:
        try:
            major = int(version.split(".")[0])
        except ValueError:
            return False

        if major < minimum_major:
            return False

    return True


def expand_template(
    value: str,
    version: str,
) -> str:
    return value.replace(
        "{version}",
        version,
    )
