"""Create a source-only GitHub snapshot using a conservative file allowlist."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = (
    ".github",
    ".streamlit",
    "docs",
    "src",
    "streamlit_app",
    "scripts",
    "tests",
)
ROOT_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    ".gitignore",
    ".gitattributes",
    ".python-version",
    "pyproject.toml",
    "uv.lock",
)
EXTRA_FILES = ("data/README.md", "data/synthetic/.gitkeep", "reports/.gitkeep")
EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".png", ".jpg", ".jpeg", ".svg"}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
}


def source_files(root):
    root = Path(root).resolve()
    files = set()
    for name in (*ROOT_FILES, *EXTRA_FILES):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"Required source file missing: {name}")
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"External link cannot be packaged: {name}")
        files.add(path)
    for name in ("LICENSE", "LICENSE.md"):
        path = root / name
        if (
            path.is_file()
            and not path.is_symlink()
            and path.resolve().is_relative_to(root)
        ):
            files.add(path)
    for name in DIRECTORIES:
        for path in (root / name).rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(root)
            if any(
                part in EXCLUDED_PARTS or part.startswith(".venv")
                for part in relative.parts
            ):
                continue
            if not path.resolve().is_relative_to(root):
                continue
            if path.suffix.lower() in EXTENSIONS:
                files.add(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_archive(root=PROJECT_ROOT):
    root = Path(root).resolve()
    files = source_files(root)
    destination = root / "dist" / "business-banking-rm-intelligence-hub-github.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(
                path, arcname=f"{root.name}/{path.relative_to(root).as_posix()}"
            )
    return destination, len(files)


if __name__ == "__main__":
    archive, count = build_archive()
    print(f"Packaged {count} source files: {archive}")
