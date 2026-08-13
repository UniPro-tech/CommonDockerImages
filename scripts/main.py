from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from config import (
    ImageConfig,
    expand_template,
    load_configs,
)
from docker import build_and_push
from sources.dockerhub import (
    get_latest_matching_tag,
    get_tags,
)
from sources.github import (
    get_latest_release_tag,
)
from state import (
    load_state,
    save_state,
)


def login_ghcr() -> None:
    registry = "ghcr.io"

    username = os.environ.get("GHCR_USERNAME")

    token = os.environ.get("GHCR_TOKEN")

    if not username:
        username = os.environ.get("GITHUB_ACTOR")

    if not token:
        token = os.environ.get("GITHUB_TOKEN")

    if not username:
        raise RuntimeError("GHCR_USERNAME or GITHUB_ACTOR is required")

    if not token:
        raise RuntimeError("GHCR_TOKEN or GITHUB_TOKEN is required")

    subprocess.run(
        [
            "docker",
            "login",
            registry,
            "--username",
            username,
            "--password-stdin",
        ],
        input=token,
        text=True,
        check=True,
    )


def is_force_build() -> bool:
    value = os.environ.get(
        "FORCE_BUILD",
        "",
    ).lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
    }


def set_github_output(
    updated: bool,
) -> None:
    output = os.environ.get("GITHUB_OUTPUT")

    if not output:
        return

    with open(
        output,
        "a",
        encoding="utf-8",
    ) as f:
        f.write(f"updated={'true' if updated else 'false'}\n")


def version_key(
    value: str,
):
    return tuple(int(x) for x in value.split(".") if x.isdigit())


def resolve_plugins(
    config: ImageConfig,
) -> dict[str, str]:
    result: dict[str, str] = {}

    for plugin in config.plugins:
        if plugin.source_type != "github_release":
            raise ValueError(f"Unsupported plugin source: {plugin.source_type}")

        latest = get_latest_release_tag(
            plugin.source_repository,
            plugin.version_pattern,
        )

        if latest is None:
            raise RuntimeError(
                f"No matching release found for {plugin.source_repository}"
            )

        result[plugin.name] = latest

    return result


def process_postgres(
    config: ImageConfig,
) -> bool:
    print("=" * 70)
    print("Checking PostgreSQL")
    print("=" * 70)

    state = load_state(config.name)

    force = is_force_build()

    # ------------------------------------------------------------
    # PostgreSQL major versions
    # ------------------------------------------------------------

    current_versions = state.get("versions", {})

    # image.yaml の minimum_major から対象majorを決める。
    #
    # 現在のPostgreSQL対応範囲は15〜18。
    #
    # 将来18以上が出た場合もDocker Hub側に存在すれば
    # 自動的に拾えるようにする。
    tags = get_tags(
        config.source_repository,
        max_pages=5,
    )

    major_versions: dict[str, str] = {}

    pattern = re.compile(config.version_pattern)

    for tag in tags:
        if not pattern.fullmatch(tag):
            continue

        try:
            major = int(tag.split(".")[0])
        except ValueError:
            continue

        if config.minimum_major is not None and major < config.minimum_major:
            continue

        if major not in major_versions or version_key(tag) > version_key(
            major_versions[major]
        ):
            major_versions[major] = tag

    if not major_versions:
        raise RuntimeError("No PostgreSQL versions found")

    # ------------------------------------------------------------
    # pg_bigm
    # ------------------------------------------------------------

    plugin_versions = resolve_plugins(config)

    pg_bigm_version = plugin_versions.get("pg_bigm")

    if not pg_bigm_version:
        raise RuntimeError("pg_bigm version was not resolved")

    changed = False

    for major in sorted(
        major_versions,
        key=int,
    ):
        postgres_version = major_versions[major]

        previous = current_versions.get(major, {})

        previous_postgres = previous.get("postgres_version")

        previous_bigm = previous.get("pg_bigm_version")

        needs_build = (
            force
            or previous_postgres != postgres_version
            or previous_bigm != pg_bigm_version
        )

        print(f"PostgreSQL {major}: {previous_postgres} -> {postgres_version}")

        print(f"pg_bigm: {previous_bigm} -> {pg_bigm_version}")

        if not needs_build:
            print("No update.")
            continue

        print("Build required.")

        build_args = {
            "PG_VERSION": postgres_version,
            "PG_BIGM_VERSION": pg_bigm_version,
        }

        image = (
            f"{config.target_registry}/{config.target_repository}:{postgres_version}"
        )

        build_and_push(
            dockerfile=config.dockerfile,
            context=config.dockerfile.parent,
            image=image,
            build_args=build_args,
        )

        current_versions[major] = {
            "postgres_version": postgres_version,
            "pg_bigm_version": pg_bigm_version,
        }

        changed = True

    if changed:
        state["versions"] = current_versions

        state["latest"] = max(
            major_versions.values(),
            key=version_key,
        )

        save_state(
            config.name,
            state,
        )

    return changed


def process_seafile(
    config: ImageConfig,
) -> bool:
    print("=" * 70)
    print("Checking Seafile")
    print("=" * 70)

    state = load_state(config.name)

    force = is_force_build()

    latest = get_latest_matching_tag(
        config.source_repository,
        config.version_pattern,
        max_pages=5,
    )

    if latest is None:
        raise RuntimeError("No matching Seafile version found")

    current = state.get("version")

    print(f"Current: {current}")

    print(f"Latest:  {latest}")

    needs_build = force or current != latest

    if not needs_build:
        print("No update.")

        return False

    print("Build required.")

    build_args = {}

    for key, value in config.build_args.items():
        build_args[key] = expand_template(
            value,
            latest,
        )

    # ------------------------------------------------------------
    # メインタグ
    # ------------------------------------------------------------

    main_image = f"{config.target_registry}/{config.target_repository}:{latest}"

    build_and_push(
        dockerfile=config.dockerfile,
        context=config.dockerfile.parent,
        image=main_image,
        build_args=build_args,
    )

    # ------------------------------------------------------------
    # 追加タグ
    # ------------------------------------------------------------

    for tag_template in config.tags:
        tag = expand_template(
            tag_template,
            latest,
        )

        # {version} はmain_imageと同じなのでスキップ
        if tag == latest:
            continue

        target = f"{config.target_registry}/{config.target_repository}:{tag}"

        print(f"Adding tag: {target}")

        subprocess.run(
            [
                "docker",
                "tag",
                main_image,
                target,
            ],
            check=True,
        )

        subprocess.run(
            [
                "docker",
                "push",
                target,
            ],
            check=True,
        )

    state["version"] = latest

    save_state(
        config.name,
        state,
    )

    return True


def process_generic(
    config: ImageConfig,
) -> bool:
    print("=" * 70)
    print(f"Checking {config.name}")
    print("=" * 70)

    state = load_state(config.name)

    force = is_force_build()

    latest = get_latest_matching_tag(
        config.source_repository,
        config.version_pattern,
        minimum_major=config.minimum_major,
        max_pages=5,
    )

    if latest is None:
        raise RuntimeError(f"No matching version found for {config.name}")

    current = state.get("version")

    print(f"Current: {current}")

    print(f"Latest: {latest}")

    if not force and current == latest:
        print("No update.")

        return False

    build_args = {}

    for key, value in config.build_args.items():
        build_args[key] = expand_template(
            value,
            latest,
        )

    image = f"{config.target_registry}/{config.target_repository}:{latest}"

    build_and_push(
        dockerfile=config.dockerfile,
        context=config.dockerfile.parent,
        image=image,
        build_args=build_args,
    )

    state["version"] = latest

    save_state(
        config.name,
        state,
    )

    return True


def process(
    config: ImageConfig,
) -> bool:
    if config.name == "postgres":
        return process_postgres(config)

    if config.name == "seafile":
        return process_seafile(config)

    return process_generic(config)


def main() -> None:
    login_ghcr()

    configs = load_configs()

    print(f"Loaded {len(configs)} image configuration(s)")

    for config in configs:
        print(f"  - {config.name}")

    updated = False

    for config in configs:
        changed = process(config)

        if changed:
            updated = True

    set_github_output(updated)

    print("=" * 70)

    if updated:
        print("Updates were built and pushed.")
    else:
        print("No updates.")


if __name__ == "__main__":
    main()
