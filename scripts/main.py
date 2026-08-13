from __future__ import annotations

import os
import re

from config import (
    expand_template,
    load_configs,
    version_matches,
)
from docker import build_and_push, push_tag
from registry import login_ghcr
from sources.dockerhub import get_tags
from sources.github import get_release_tags
from state import load_state, save_state


def version_key(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)

    return tuple(int(part) for part in parts)


def get_latest_version(
    tags: list[str],
    pattern: str,
    minimum_major: int | None = None,
) -> str | None:
    versions = [
        tag
        for tag in tags
        if version_matches(
            pattern,
            tag,
            minimum_major,
        )
    ]

    if not versions:
        return None

    return max(
        versions,
        key=version_key,
    )


def get_plugin_versions(plugin):
    if plugin.source_type == "github_release":
        return get_release_tags(plugin.source_repository)

    raise RuntimeError(f"Unsupported plugin source: {plugin.source_type}")


def get_latest_plugin_version(plugin):
    tags = get_plugin_versions(plugin)

    return get_latest_version(
        tags,
        plugin.version_pattern,
    )


def process_postgres(config) -> bool:
    print()
    print("=" * 70)
    print("Checking PostgreSQL")
    print("=" * 70)

    tags = get_tags(config.source_repository)

    postgres_versions = [
        tag
        for tag in tags
        if version_matches(
            config.version_pattern,
            tag,
            config.minimum_major,
        )
    ]

    postgres_versions.sort(key=version_key)

    state = load_state(config.name)

    updated = False

    pg_bigm_version = None

    for plugin in config.plugins:
        pg_bigm_version = get_latest_plugin_version(plugin)

        print(f"{plugin.name}: {pg_bigm_version}")

    if pg_bigm_version is None:
        raise RuntimeError("pg_bigm version was not found")

    for pg_version in postgres_versions:
        major = pg_version.split(".")[0]

        current = state.get(major, {})

        current_pg = current.get("postgres_version")

        current_bigm = current.get("pg_bigm_version")

        print(f"PostgreSQL {major}: {current_pg} -> {pg_version}")

        print(f"pg_bigm: {current_bigm} -> {pg_bigm_version}")

        if current_pg == pg_version and current_bigm == pg_bigm_version:
            print("No update.")
            continue

        print(f"Building PostgreSQL {pg_version}")

        build_args = {
            "PG_VERSION": pg_version,
            "PG_MAJOR": major,
            "PG_BIGM_VERSION": pg_bigm_version,
        }

        local_image = f"{config.target_repository}:{pg_version}"

        build_and_push(
            dockerfile=config.dockerfile,
            context=config.dockerfile.parent,
            image=local_image,
            build_args=build_args,
        )

        for tag_template in config.tags:
            tag = expand_template(
                tag_template,
                pg_version,
            )

            target_image = f"{config.target_registry}/{config.target_repository}:{tag}"

            if target_image != local_image:
                push_tag(
                    local_image,
                    target_image,
                )

        state[major] = {
            "postgres_version": pg_version,
            "pg_bigm_version": pg_bigm_version,
        }

        updated = True

    save_state(
        config.name,
        state,
    )

    return updated


def process_generic_image(config) -> bool:
    print()
    print("=" * 70)
    print(f"Checking {config.name}")
    print("=" * 70)

    tags = get_tags(config.source_repository)

    latest = get_latest_version(
        tags,
        config.version_pattern,
        config.minimum_major,
    )

    if latest is None:
        print("No matching version found.")
        return False

    state = load_state(config.name)

    current = state.get("version")

    print(f"Current: {current}")

    print(f"Latest: {latest}")

    if current == latest:
        print("No update.")
        return False

    build_args = {"VERSION": latest}

    local_image = f"{config.target_repository}:{latest}"

    build_and_push(
        dockerfile=config.dockerfile,
        context=config.dockerfile.parent,
        image=local_image,
        build_args=build_args,
    )

    for tag_template in config.tags:
        tag = expand_template(
            tag_template,
            latest,
        )

        target_image = f"{config.target_registry}/{config.target_repository}:{tag}"

        if target_image != local_image:
            push_tag(
                local_image,
                target_image,
            )

    state["version"] = latest

    save_state(
        config.name,
        state,
    )

    return True


def main():
    login_ghcr()

    configs = load_configs()

    updated = False

    for config in configs:
        if config.name == "postgres":
            changed = process_postgres(config)
        else:
            changed = process_generic_image(config)

        if changed:
            updated = True

    output = os.environ.get("GITHUB_OUTPUT")

    if output:
        with open(output, "a") as f:
            f.write("updated=" + ("true" if updated else "false") + "\n")


if __name__ == "__main__":
    main()
