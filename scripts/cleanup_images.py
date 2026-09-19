"""Remove images on disk not referenced by any service JSON.

Scans `data/<country>/*.json` files for `image` fields that reference local
files under `data/<country>/img/` and deletes files in those img folders that
are not referenced. Use `--dry-run` to preview.
"""
from __future__ import annotations

import argparse
import os
import json
from typing import Set


def find_json_files(data_root: str):
    for root, dirs, files in os.walk(data_root):
        for f in files:
            if f.endswith('.json'):
                yield os.path.join(root, f)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_root = os.path.join(base, "data")

    referenced: Set[str] = set()
    for jf in find_json_files(data_root):
        try:
            with open(jf, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if isinstance(data, dict):
            # top-level dict (maybe rotten_top300) has no images
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            img = item.get('image')
            if not img:
                continue
            # consider only local data/ paths
            if isinstance(img, str) and img.startswith('data' + os.sep):
                referenced.add(os.path.normpath(os.path.join(base, img)))

    # find all img files and delete unreferenced
    deleted = 0
    checked = 0
    for country in os.listdir(data_root):
        cpath = os.path.join(data_root, country)
        if not os.path.isdir(cpath):
            continue
        img_root = os.path.join(cpath, "img")
        if not os.path.isdir(img_root):
            continue
        for root, dirs, files in os.walk(img_root):
            for f in files:
                checked += 1
                full = os.path.join(root, f)
                if os.path.normpath(full) not in referenced:
                    if args.dry_run:
                        print("Would remove", full)
                    else:
                        try:
                            os.remove(full)
                            deleted += 1
                        except Exception as e:
                            print("Failed to remove", full, e)

    print(f"Checked {checked} images, deleted {deleted}")


if __name__ == "__main__":
    main()
