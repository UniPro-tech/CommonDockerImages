from __future__ import annotations

import subprocess
from pathlib import Path


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
        "-f",
        str(dockerfile),
        "-t",
        image,
    ]

    for key, value in build_args.items():
        command.extend(
            [
                "--build-arg",
                f"{key}={value}",
            ]
        )

    command.append(str(context))

    print("Running:", " ".join(command))

    subprocess.run(command, check=True)

    subprocess.run(
        [
            "docker",
            "push",
            image,
        ],
        check=True,
    )


def push_tag(source_image: str, target_image: str) -> None:
    subprocess.run(
        [
            "docker",
            "tag",
            source_image,
            target_image,
        ],
        check=True,
    )

    subprocess.run(
        [
            "docker",
            "push",
            target_image,
        ],
        check=True,
    )
