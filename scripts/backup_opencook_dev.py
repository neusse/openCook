"""Save and verify the complete private state of the connected openCook DEV app."""

import argparse
import hashlib
import json
import sqlite3
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "com.food.opencook.dev"


def adb(serial, *args):
    return subprocess.run(["adb", "-s", serial, *args], check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="Exact ADB serial of the owner's openCook phone")
    args = parser.parse_args()
    serial = args.serial
    devices = adb(serial, "get-state").stdout.strip()
    if devices != "device":
        raise RuntimeError(f"ADB device {serial} is not ready: {devices}")
    if not adb(serial, "shell", "pm", "list", "packages", PACKAGE).stdout.strip().endswith(PACKAGE):
        raise RuntimeError(f"{PACKAGE} is not installed on {serial}")
    adb(serial, "shell", "run-as", PACKAGE, "pwd")
    adb(serial, "shell", "am", "force-stop", PACKAGE)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = ROOT / "data/phone-backups" / f"{stamp}-{serial}-opencook-dev"
    folder.mkdir(parents=True, exist_ok=False)
    part = folder / "opencook-dev.tar.part"
    archive = folder / "opencook-dev.tar"
    error_file = folder / "adb-stderr.txt"
    digest = hashlib.sha256()
    count = 0
    with error_file.open("wb") as errors, part.open("wb") as output:
        process = subprocess.Popen(
            ["adb", "-s", serial, "exec-out", "run-as", PACKAGE, "tar", "-cf", "-", "."],
            stdout=subprocess.PIPE, stderr=errors,
        )
        assert process.stdout is not None
        while chunk := process.stdout.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
            count += len(chunk)
            if count // (256 * 1024 * 1024) != (count - len(chunk)) // (256 * 1024 * 1024):
                print(f"Copied {count / 1024**3:.2f} GiB", flush=True)
        code = process.wait()
    if code != 0 or count < 100_000_000:
        raise RuntimeError(f"ADB tar failed (exit {code}, {count} bytes); see {error_file}")
    part.replace(archive)
    with tarfile.open(archive, "r") as saved:
        members = saved.getmembers()
        names = {member.name.lstrip("./") for member in members}
        database = next((name for name in names if name == "databases/opencook.db"), None)
        image_files = [name for name in names if name.startswith("files/") and name.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        if database is None:
            raise RuntimeError("Backup is missing databases/opencook.db")
        for name in ("databases/opencook.db", "databases/opencook.db-wal", "databases/opencook.db-shm"):
            member = next((item for item in members if item.name.lstrip("./") == name), None)
            if member:
                source = saved.extractfile(member)
                assert source is not None
                with (folder / Path(name).name).open("wb") as target:
                    while chunk := source.read(1024 * 1024):
                        target.write(chunk)
    connection = sqlite3.connect(f"file:{folder / 'opencook.db'}?mode=ro", uri=True)
    if connection.execute("pragma quick_check").fetchone()[0] != "ok":
        raise RuntimeError("Backed-up SQLite database failed quick_check")
    image_paths = [row[0] for row in connection.execute("select localPath from images where localPath is not null")]
    prefix = f"/data/user/0/{PACKAGE}/"
    missing = [path for path in image_paths if not path.startswith(prefix) or path[len(prefix):] not in names]
    if missing:
        raise RuntimeError(f"Backup is missing database-referenced images: {missing[:5]}")
    metadata = {
        "serial": serial,
        "package": PACKAGE,
        "capturedUtc": stamp,
        "archive": archive.name,
        "bytes": count,
        "sha256": digest.hexdigest(),
        "entries": len(members),
        "imageFiles": len(image_files),
        "imageRecords": len(image_paths),
        "database": database,
    }
    (folder / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2), flush=True)
    print(f"Backup: {folder}", flush=True)


if __name__ == "__main__":
    main()
