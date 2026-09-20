"""
Fetch the two United Nations World Population Prospects 2024 files that this
analysis needs.

These are not redistributed in this repository. They are the single-age
population files from the wpp2024 R data package maintained by the United
Nations Population Division, which carries its own licence; consult that
licence and the United Nations terms of use before redistributing them.

Usage:  python scripts/fetch_wpp.py
"""

import hashlib
import os
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/PPgp/wpp2024/master/data"
FILES = {
    "popprojAge1dt.rda": "population projections by single age, 2024 to 2100",
    "popAge1dt.rda": "estimated population by single age, historical",
}
DEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data")


def sha256(path, blocks=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(blocks), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(DEST, exist_ok=True)
    for name, what in FILES.items():
        out = os.path.join(DEST, name)
        if os.path.exists(out):
            print(f"  present  {name}  ({what})")
            continue
        url = f"{BASE}/{name}"
        print(f"  fetching {name}  ({what})")
        try:
            urllib.request.urlretrieve(url, out)
        except Exception as exc:                       # noqa: BLE001
            print(f"  FAILED   {name}: {exc}", file=sys.stderr)
            print(f"  download it manually from {url}", file=sys.stderr)
            sys.exit(1)
        size = os.path.getsize(out) / 1048576
        print(f"           {size:.1f} MB, sha256 {sha256(out)[:16]}...")
    print("\nDone. Run `make analysis` next.")


if __name__ == "__main__":
    main()
