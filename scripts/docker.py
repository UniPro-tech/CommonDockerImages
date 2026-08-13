from __future__ import annotations

import subprocess
from pathlib import Path


def run(
    command: list[str],
) -> None:
    print(
        "$",
        " ".join(command),
        flush=True,
    )

    subprocess.run(
        command,
        check=True,
    )


def build_and_push(
    *,
    dockerfile: Path,
    context: Path,
    image: str,
    build_args: dict[str, str],
) -> None:
    command = [
        "docker",
        "build",
        "--file",
        str(dockerfile),
    ]

    for key, value in build_args.items():
        command.extend(
            [
                "--build-arg",
                f"{key}={value}",
            ]
        )

    command.extend(
        [
            "--tag",
            image,
            str(context),
        ]
    )

    run(command)

    run(
        [
            "docker",
            "push",
            image,
        ]
    )


def tag_and_push(
    source: str,
    target: str,
) -> None:
    run(
        [
            "docker",
            "tag",
            source,
            target,
        ]
    )

    run(
        [
            "docker",
            "push",
            target,
        ]
    )
