#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  vault.py -- the MAINFRAME discipline for OPAQUE BLOBS (sibling of redundancy.py)
# ----------------------------------------------------------------------------
#  The rule Vlad set: no matter how small or big, WE TRIPLICATE.
#
#  Helena/redundancy.py vaults TYPED ARRAYS (.f32/.i32/.f64) and votes per
#  ELEMENT. This vaults OPAQUE BLOBS -- JSON exports, which have no element
#  type -- so THE ATOM HERE IS THE BYTE, declared rather than assumed. Two
#  files, two jobs, no duplication: redundancy.py owns the net, vault.py
#  owns the exports. Otherwise the structure is hers, unchanged:
#
#    1) .bin  -- raw bytes                       (compact, fast)
#    2) .csv  -- flat text records, "index,hex"  (COBOL flat file: a bit flip
#                damages ONE line, and a human can find it with their eyes)
#    3) .zip  -- stdlib archive with CRC32       (self-checking codec)
#
#  SHA-256 MANIFEST.json of the canonical bytes plus every copy. Repair is
#  TMR: byte-wise majority vote -- one flipped bit loses 2-to-1.
#
#  SCOPE, honestly: git-tracked text already lives three times (working tree,
#  .git objects, remote). This vault is for the GITIGNORED payload lane --
#  Eleni/exports/, which git never holds. The MANIFEST is tracked (Curse 31:
#  the steps, not the payload); the three copies stay local.
#
#      py -3 Eleni/builder/vault.py selftest              # flip a bit, heal it, prove it
#      py -3 Eleni/builder/vault.py save   FILE [FILE..]  # write the 3-format vault
#      py -3 Eleni/builder/vault.py verify FILE           # every copy vs manifest
#      py -3 Eleni/builder/vault.py repair FILE           # TMR-vote and heal
# ============================================================================
import base64
import hashlib
import json
import os
import sys
import time
import zipfile

BYTES_PER_LINE = 32


def sha(b):
    return hashlib.sha256(b).hexdigest()


def vdir(path):
    return os.path.join(os.path.dirname(os.path.abspath(path)) or ".", "vault")


def _paths(path):
    base = os.path.basename(path)
    d = vdir(path)
    return d, {
        "bin": os.path.join(d, base + ".bin"),
        "csv": os.path.join(d, base + ".csv"),
        "zip": os.path.join(d, base + ".zip"),
        "man": os.path.join(d, "MANIFEST.json"),
    }


def _to_csv(raw):
    out = []
    for i in range(0, len(raw), BYTES_PER_LINE):
        out.append("%d,%s" % (i // BYTES_PER_LINE, raw[i:i + BYTES_PER_LINE].hex()))
    return ("\n".join(out) + "\n").encode("ascii")


def _from_csv(data):
    chunks = []
    for ln in data.decode("ascii", "replace").splitlines():
        if not ln.strip():
            continue
        chunks.append(bytes.fromhex(ln.split(",", 1)[1]))
    return b"".join(chunks)


def _read_copy(p, fmt, inner):
    try:
        if fmt == "bin":
            return open(p, "rb").read()
        if fmt == "csv":
            return _from_csv(open(p, "rb").read())
        if fmt == "zip":
            with zipfile.ZipFile(p) as z:
                return z.read(inner)
    except Exception:
        return None
    return None


def save(path):
    raw = open(path, "rb").read()
    d, p = _paths(path)
    os.makedirs(d, exist_ok=True)
    base = os.path.basename(path)
    open(p["bin"], "wb").write(raw)
    open(p["csv"], "wb").write(_to_csv(raw))
    with zipfile.ZipFile(p["zip"], "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(base, raw)
    man = {}
    if os.path.exists(p["man"]):
        man = json.load(open(p["man"], encoding="utf-8"))
    man[base] = {
        "sha256": sha(raw), "bytes": len(raw),
        "atom": "byte (JSON has no element type -- declared, per vault.py)",
        "copies": {f: sha(_read_copy(p[f], f, base)) for f in ("bin", "csv", "zip")},
        "vaulted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "HELENA redundancy.py, mirrored -- 3 codecs, SHA-256, TMR",
    }
    json.dump(man, open(p["man"], "w", encoding="utf-8"), indent=1, sort_keys=True)
    print("  vaulted %s  (%d B x3: bin csv zip)  sha %s..." % (base, len(raw), sha(raw)[:16]))


def verify(path, quiet=False):
    base = os.path.basename(path)
    d, p = _paths(path)
    man = json.load(open(p["man"], encoding="utf-8"))[base]
    good, bad = [], []
    for f in ("bin", "csv", "zip"):
        raw = _read_copy(p[f], f, base)
        (good if raw is not None and sha(raw) == man["sha256"] else bad).append(f)
    if not quiet:
        for f in good:
            print("  %s: OK" % f)
        for f in bad:
            print("  %s: CORRUPT" % f)
        v = "ALL 3 COPIES VERIFIED" if not bad else (
            "%d bad -> repairable" % len(bad) if len(good) >= 2 else "AT RISK: <2 good copies")
        print("  " + v)
    return good, bad, man


def repair(path):
    base = os.path.basename(path)
    d, p = _paths(path)
    man = json.load(open(p["man"], encoding="utf-8"))[base]
    cands = [c for c in (_read_copy(p[f], f, base) for f in ("bin", "csv", "zip"))
             if c is not None and len(c) == man["bytes"]]
    if len(cands) < 2:
        sys.exit("  CANNOT REPAIR: fewer than 2 same-length copies")
    voted = bytearray(man["bytes"])
    outvoted = 0
    for i in range(man["bytes"]):
        vals = [c[i] for c in cands]
        win = max(set(vals), key=vals.count)
        if vals.count(win) < 2:
            win = vals[0]
        if any(v != win for v in vals):
            outvoted += 1
        voted[i] = win
    voted = bytes(voted)
    print("  vote: %d byte(s) outvoted across %d copies" % (outvoted, len(cands)))
    if sha(voted) != man["sha256"]:
        sys.exit("  REPAIR FAILED: voted bytes do not match manifest sha256")
    open(path, "wb").write(voted)
    save(path)
    print("  healed: voted bytes match manifest sha256, all copies rewritten")


def selftest():
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(), "probe.json")
    open(tmp, "wb").write(json.dumps({"p": 12, "chi": 2, "list": list(range(199))}).encode())
    save(tmp)
    d, p = _paths(tmp)
    raw = bytearray(open(p["bin"], "rb").read())
    raw[len(raw) // 2] ^= 0x10                       # the cosmic ray
    open(p["bin"], "wb").write(raw)
    print("  flipped one bit in the .bin copy")
    good, bad, _ = verify(tmp)
    assert bad == ["bin"], "verify missed the flip"
    repair(tmp)
    good, bad, _ = verify(tmp)
    assert not bad, "repair did not heal"
    print("  SELFTEST PASS: flip detected, outvoted 2-to-1, healed, re-verified")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__ or "vault.py: selftest | save FILE.. | verify FILE | repair FILE")
    cmd = sys.argv[1]
    if cmd == "selftest":
        selftest()
    elif cmd == "save":
        for f in sys.argv[2:]:
            save(f)
    elif cmd == "verify":
        verify(sys.argv[2])
    elif cmd == "repair":
        repair(sys.argv[2])
    else:
        sys.exit("unknown command: " + cmd)
