from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from submission import build_submission_file_list, create_submission_zip


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a compact course submission package")
    parser.add_argument("--output", default="dist/beidou_positioning_submission.zip", help="Output zip path")
    parser.add_argument("--manifest", default="dist/submission_manifest.txt", help="Output manifest path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    files = build_submission_file_list(root)
    package_path = create_submission_zip(root, args.output, files)

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(path.as_posix() for path in files) + "\n", encoding="utf-8")

    size_mb = package_path.stat().st_size / (1024 * 1024)
    print(f"Files: {len(files)}")
    print(f"Package: {package_path} ({size_mb:.2f} MB)")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
