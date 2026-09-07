#!/usr/bin/env python3
"""Build clean, deterministic skill archives from the runtime allowlist."""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile


ROOT_FILES = ("SKILL.md", "LICENSE", "LICENSE.txt", "NOTICE")
RUNTIME_DIRECTORIES = (
    "agents",
    "assets",
    "examples",
    "references",
    "schemas",
    "scripts",
    "templates",
)
IGNORED_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}
IGNORED_NAMES = {"changelog.md", "readme.md"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp"}
ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(Exception):
    pass


def validate_skill(skill: Path) -> str:
    if not skill.is_dir():
        raise PackageError(f"skill directory not found: {skill}")
    entrypoint = skill / "SKILL.md"
    if not entrypoint.is_file():
        raise PackageError(f"missing entrypoint: {entrypoint}")
    text = entrypoint.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.DOTALL)
    if not match:
        raise PackageError("SKILL.md must start with YAML front matter")
    front_matter = match.group(1)
    name_match = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", front_matter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+)$", front_matter, re.MULTILINE)
    if not name_match or not description_match or not description_match.group(1).strip():
        raise PackageError("SKILL.md front matter needs non-empty name and description fields")
    name = name_match.group(1)
    if name != skill.name:
        raise PackageError(f"skill name '{name}' does not match directory '{skill.name}'")
    if len(name) > 64:
        raise PackageError("skill name exceeds 64 characters")
    return name


def include_file(path: Path, relative: Path) -> bool:
    if path.is_symlink():
        raise PackageError(f"symbolic links are not allowed in the package: {path}")
    if any(part.startswith(".") or part in IGNORED_PARTS for part in relative.parts):
        return False
    if path.name.casefold() in IGNORED_NAMES:
        return False
    if path.suffix.lower() in IGNORED_SUFFIXES or path.name.endswith("~"):
        return False
    return path.is_file()


def runtime_files(skill: Path) -> list[Path]:
    files = []
    for name in ROOT_FILES:
        path = skill / name
        if path.exists() and include_file(path, path.relative_to(skill)):
            files.append(path)
    for directory_name in RUNTIME_DIRECTORIES:
        directory = skill / directory_name
        if not directory.exists():
            continue
        if not directory.is_dir() or directory.is_symlink():
            raise PackageError(f"runtime path must be a directory: {directory}")
        for path in directory.rglob("*"):
            relative = path.relative_to(skill)
            if include_file(path, relative):
                files.append(path)
    files.sort(key=lambda item: item.relative_to(skill).as_posix())
    if skill / "SKILL.md" not in files:
        raise PackageError("runtime allowlist did not include SKILL.md")
    return files


def archive_name(skill: Path, source: Path, wrapped: bool) -> str:
    relative = source.relative_to(skill).as_posix()
    return f"{skill.name}/{relative}" if wrapped else relative


def file_mode(path: Path) -> int:
    if path.suffix in {".py", ".sh"} and path.read_bytes().startswith(b"#!"):
        return 0o755
    return 0o644


def build_archive(skill: Path, files: list[Path], output: Path, wrapped: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for source in files:
                name = archive_name(skill, source, wrapped)
                pure_name = PurePosixPath(name)
                if pure_name.is_absolute() or ".." in pure_name.parts:
                    raise PackageError(f"unsafe archive path: {name}")
                info = zipfile.ZipInfo(name, ARCHIVE_TIMESTAMP)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (file_mode(source) & 0xFFFF) << 16
                archive.writestr(info, source.read_bytes(), compresslevel=9)
        expected_entrypoint = f"{skill.name}/SKILL.md" if wrapped else "SKILL.md"
        with zipfile.ZipFile(temporary) as archive:
            names = archive.namelist()
            if expected_entrypoint not in names:
                raise PackageError(f"archive is missing {expected_entrypoint}")
            if len(names) != len(set(names)):
                raise PackageError("archive contains duplicate entries")
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path, help="path to the skill directory")
    parser.add_argument("--output", type=Path, required=True, help="flat .skill archive")
    parser.add_argument(
        "--wrapped-output",
        type=Path,
        help="optional ZIP with the skill directory as its top-level folder",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        skill = args.skill.resolve()
        name = validate_skill(skill)
        files = runtime_files(skill)
        build_archive(skill, files, args.output.resolve(), wrapped=False)
        print(f"Built {args.output} ({len(files)} runtime files, SKILL.md at archive root).")
        if args.wrapped_output:
            build_archive(skill, files, args.wrapped_output.resolve(), wrapped=True)
            print(
                f"Built {args.wrapped_output} ({len(files)} runtime files, "
                f"top-level {name}/ folder)."
            )
    except (OSError, UnicodeError, PackageError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"package_skill: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
