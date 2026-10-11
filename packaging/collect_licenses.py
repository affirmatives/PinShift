"""Collect installed dependency notices and versions for the macOS bundle."""

from __future__ import annotations

import json
import platform
import re
import shutil
from importlib.metadata import distributions
from pathlib import Path


def collect_licenses(root: Path) -> Path:
    destination = root / "build" / "third-party-licenses"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copytree(root / "licenses" / "upstream", destination / "upstream")

    components = []
    for distribution in sorted(distributions(), key=lambda item: item.metadata["Name"].lower()):
        name = distribution.metadata["Name"]
        directory_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", f"{name}-{distribution.version}")
        license_files = []
        for entry in distribution.files or []:
            if not any(
                part.lower().startswith(("license", "copying", "notice"))
                for part in entry.parts
            ):
                continue
            source = Path(distribution.locate_file(entry))
            if not source.is_file():
                continue
            # Keep vendored license paths while preventing traversal out of the bundle.
            relative = Path(*(part for part in entry.parts if part not in ("..", ".")))
            target = destination / "packages" / directory_name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            license_files.append(target.relative_to(destination).as_posix())

        components.append({
            "name": name,
            "version": distribution.version,
            "license": distribution.metadata.get("License-Expression")
            or distribution.metadata.get("License"),
            "project_urls": distribution.metadata.get_all("Project-URL") or [],
            "homepage": distribution.metadata.get("Home-page"),
            "author": distribution.metadata.get("Author"),
            "license_files": sorted(license_files),
        })

    inventory = {
        "scope": "Build environment inventory; includes build tools and optional dependencies.",
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "components": components,
    }
    (destination / "BUILD_DEPENDENCIES.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "requirements-build.txt").write_text(
        "# Snapshot of this build environment, including build tools.\n"
        + "\n".join(f'{item["name"]}=={item["version"]}' for item in components)
        + "\n", encoding="utf-8"
    )
    print(f"Collected dependency notices and versions for {len(components)} distributions.")
    return destination


if __name__ == "__main__":
    collect_licenses(Path(__file__).resolve().parents[1])
