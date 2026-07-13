import requests
import re
import os
import subprocess
from state import load_state, save_state

DOCKERFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "official", "postgres", "Dockerfile"
)


def get_latest_pg_bigm_version():
    url = "https://api.github.com/repos/pgbigm/pg_bigm/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["tag_name"].lstrip("v")


def compare_versions(v1, v2):
    v1_parts = list(map(int, v1.split(".")))
    v2_parts = list(map(int, v2.split(".")))
    return (v1_parts > v2_parts) - (v1_parts < v2_parts)


def get_target_postgres_versions():
    """15以上のメジャーバージョンごとの最新マイナーバージョンを取得"""
    url = "https://hub.docker.com/v2/repositories/library/postgres/tags/?page_size=100"
    versions = {}

    while url:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for r in data.get("results", []):
            name = r["name"]
            # 純粋なバージョンの数字だけ（例: 15.3, 16.0）
            if re.match(r"^\d+\.\d+$", name):
                major = name.split(".")[0]
                if int(major) >= 15:
                    if (
                        major not in versions
                        or compare_versions(name, versions[major]) > 0
                    ):
                        versions[major] = name

        url = data.get("next")  # 次ページがある場合は取得
    return versions


def update_dockerfile_defaults(pg_version, pg_bigm_version):
    """DockerfileのデフォルトARGを全体での最新バージョンに書き換える"""
    with open(DOCKERFILE_PATH, "r") as f:
        content = f.read()

    content = re.sub(r"ARG PG_VERSION=.*", f"ARG PG_VERSION={pg_version}", content)
    content = re.sub(
        r"ARG PG_BIGM_VERSION=.*", f"ARG PG_BIGM_VERSION={pg_bigm_version}", content
    )

    with open(DOCKERFILE_PATH, "w") as f:
        f.write(content)


def main():
    current_state = load_state()
    latest_pg_versions = get_target_postgres_versions()
    latest_bigm = get_latest_pg_bigm_version()

    updates_made = False
    overall_latest_pg = "15.0"

    for major, latest_pg in sorted(latest_pg_versions.items(), key=lambda x: int(x[0])):
        if compare_versions(latest_pg, overall_latest_pg) > 0:
            overall_latest_pg = latest_pg

        state_for_major = current_state.get(major, {})
        current_pg = state_for_major.get("postgres_version")
        current_bigm = state_for_major.get("pg_bigm_version")

        if current_pg != latest_pg or current_bigm != latest_bigm:
            print(
                f"[Update Found] Major {major}: Postgres {current_pg} -> {latest_pg}, pg_bigm {current_bigm} -> {latest_bigm}"
            )

            # build.py にバージョン情報を渡して実行
            build_script = os.path.join(os.path.dirname(__file__), "build.py")
            subprocess.run(
                ["python", build_script, major, latest_pg, latest_bigm], check=True
            )

            current_state[major] = {
                "postgres_version": latest_pg,
                "pg_bigm_version": latest_bigm,
            }
            updates_made = True
        else:
            print(
                f"[No Update] Major {major}: Postgres={current_pg}, pg_bigm={current_bigm}"
            )

    if updates_made:
        update_dockerfile_defaults(overall_latest_pg, latest_bigm)
        save_state(current_state)

        # Actionsの次のステップ（コミット）へフラグを渡す
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("updated=true\n")
    else:
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("updated=false\n")


if __name__ == "__main__":
    main()
