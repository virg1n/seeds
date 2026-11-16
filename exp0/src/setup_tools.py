"""Downloads a Java runtime (if needed) and the JPlag jar into exp0/tools/ (~60 MB)."""
from __future__ import annotations

import re
import shutil
import subprocess
import tarfile

import requests

from . import config as C
from .utils import log

JAVA_MIN = 25  # JPlag 6.3 is compiled for Java 25 (class file 69)
JRE_URL = f"https://api.adoptium.net/v3/binary/latest/{JAVA_MIN}/ga/linux/x64/jre/hotspot/normal/eclipse"
JPLAG_API = "https://api.github.com/repos/jplag/JPlag/releases"
JPLAG_URL = "https://github.com/jplag/JPlag/releases/download/v6.3.0/jplag-6.3.0-jar-with-dependencies.jar"  # pinned


def _java_version(java):
    try:
        p = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=30)
        m = re.search(r'version "(\d+)(?:\.(\d+))?', p.stderr + p.stdout)
        if not m:
            return 0
        major = int(m.group(1))
        return int(m.group(2) or 0) if major == 1 else major
    except Exception:
        return 0


def _download(url, dest):
    with requests.get(url, stream=True, timeout=300, allow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def find_java():
    import os
    cands = [os.environ["JAVA_BIN"]] if os.environ.get("JAVA_BIN") else []
    cands += [str(j) for j in sorted(C.TOOLS_DIR.glob("jre*/bin/java"))] + [shutil.which("java") or ""]
    for j in cands:
        if j and _java_version(j) >= JAVA_MIN:
            return j
    return None


def ensure_java():
    j = find_java()
    if j:
        return j
    C.TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    tgz = C.TOOLS_DIR / "jre.tar.gz"
    log(f"downloading Temurin JRE {JAVA_MIN} for JPlag ...")
    _download(JRE_URL, tgz)
    with tarfile.open(tgz) as tf:
        top = tf.getnames()[0].split("/")[0]
        tf.extractall(C.TOOLS_DIR)
    tgz.unlink()
    (C.TOOLS_DIR / top).rename(C.TOOLS_DIR / f"jre{JAVA_MIN}")
    return find_java()


def jplag_jar():
    return C.TOOLS_DIR / "jplag.jar"


def _latest_jplag_url():
    rel = requests.get(JPLAG_API, timeout=60).json()
    for r in rel:
        if r.get("prerelease") or r.get("draft"):
            continue
        for a in r.get("assets", []):
            if a["name"].endswith("jar-with-dependencies.jar"):
                return a["browser_download_url"]
    return None


def ensure_jplag():
    jar = jplag_jar()
    if jar.exists() and jar.stat().st_size > 1_000_000:
        return jar
    C.TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    url = JPLAG_URL
    try:
        if requests.head(url, timeout=60, allow_redirects=True).status_code >= 400:
            url = _latest_jplag_url()
    except Exception as e:  # noqa
        log(f"JPlag release lookup failed: {e}")
    if not url:
        raise RuntimeError("no JPlag release found")
    log(f"downloading JPlag: {url}")
    _download(url, jar)
    return jar


def main():
    try:
        j = ensure_java()
        jar = ensure_jplag()
        log(f"java: {j} (v{_java_version(j) if j else '-'}), jplag: {jar}")
    except Exception as e:  # noqa
        log(f"WARNING: JPlag setup failed ({e}); the JPlag baseline will be skipped")


if __name__ == "__main__":
    main()
