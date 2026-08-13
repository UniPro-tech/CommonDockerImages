from __future__ import annotations

import re

import requests


SESSION = requests.Session()

SESSION.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CommonDockerImages/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
)


def get_latest_release_tag(
    repository: str,
    pattern: str,
) -> str | None:
    """
    GitHub Releasesから、指定されたpatternに一致する
    最新のrelease tagを取得する。

    tagはGitHub上の値をそのまま返す。

    例:
        v1.2-20250903
    """

    url = f"https://api.github.com/repos/{repository}/releases"

    releases = []

    while url:
        response = SESSION.get(
            url,
            params={
                "per_page": 100,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected GitHub API response for {repository}")

        releases.extend(data)

        # GitHub APIのページネーション
        url = response.links.get(
            "next",
            {},
        ).get("url")

        # 100件以上存在する可能性はあるが、
        # releasesとしては十分取得できるため、
        # nextがなくなるまで取得する。

    regex = re.compile(pattern)

    versions: list[str] = []

    for release in releases:
        # Draftは除外
        if release.get("draft"):
            continue

        # Pre-releaseは除外
        if release.get("prerelease"):
            continue

        tag = release.get("tag_name")

        if not tag:
            continue

        # GitHub上のtagをそのまま比較する。
        #
        # 例:
        #   v1.2-20250903
        #
        if regex.fullmatch(tag):
            versions.append(tag)

    if not versions:
        return None

    return max(
        versions,
        key=_version_key,
    )


def _version_key(value: str) -> tuple[int, ...]:
    """
    GitHub tagからバージョン比較用のtupleを作る。

    対応例:

        v1.2-20250903
        -> (1, 2, 20250903)

        v1.2.3
        -> (1, 2, 3)

    'v' は無視する。
    """

    normalized = value.removeprefix("v")

    # 数字の連続部分をすべて抽出する。
    numbers = re.findall(
        r"\d+",
        normalized,
    )

    if not numbers:
        return (0,)

    return tuple(int(number) for number in numbers)
