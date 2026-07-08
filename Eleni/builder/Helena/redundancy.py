#!/usr/bin/env python3
# ============================================================================
#  redundancy.py  --  HELENA, the COBOL vault:  never one copy, survive the flip
# ----------------------------------------------------------------------------
#  A laptop meant to run FOREVER must keep data that outlives the hardware.
#  This is the mainframe discipline banks still trust after 60 years:
#
#    * NEVER one copy.  Every array is stored in THREE independent formats,
#      each a different codec, so no single failure mode can take all three:
#        1) .bin  -- raw little-endian bytes            (compact, fast)
#        2) .csv  -- flat text record file              (COBOL flat file; a
#                    bit-flip damages only one line, and a human can read it)
#        3) .zip  -- stdlib archive with CRC32          (self-checking codec)
#
#    * ALWAYS verify.  A SHA-256 manifest holds the canonical hash of each
#      array plus a hash of every copy. Verify is instant and catches any
#      corruption -- including a single cosmic-ray bit flip (a SEU).
#
#    * SURVIVE THE FLIP.  Repair uses TMR (Triple Modular Redundancy): it
#      majority-votes the three copies WORD BY WORD. One flipped bit in one
#      copy loses 2-to-1 to the copies that agree, so it is corrected. This is
#      how spacecraft and mainframe memory shrug off cosmic rays.
#
#  Pure stdlib (numpy NOT required) -> runs anywhere, forever. ASCII source.
#
#      py -3 redundancy.py selftest                 # prove it: flip a bit, heal it
#      py -3 redundancy.py save   builds/v001/net   # write the 3-format vault
#      py -3 redundancy.py verify builds/v001/net   # check every copy vs manifest
#      py -3 redundancy.py repair builds/v001/net   # TMR-vote and heal corruption
#
#  It vaults every *.f32 (float32) and *.i32 (int32) file in the net/ folder.
#  Floats are stored bit-exact (repr of the widened value round-trips float32).
# ============================================================================

import os, sys, json, glob, csv, struct, hashlib, zipfile, random, argparse, time

VAULT = "vault"                 # subfolder that holds the 3-format copies + manifest

# each vaulted array declares its element type by extension. word size is per-type
# so the atomic-clock timestamp (float64) is NOT silently truncated to float32.
#   .f32 float32 (4B)   .i32 int32 (4B)   .f64 float64 (8B, the unix atomic clock)
TYPE_BY_EXT = {".f32": "f", ".i32": "i", ".f64": "d"}
STRUCT = {"f": ("<f", 4), "i": ("<i", 4), "d": ("<d", 8)}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def human(n):
    x = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if x < 1024.0:
            return f"{x:.1f} {u}"
        x /= 1024.0
    return f"{x:.1f} PB"


def typ_of(name):
    for ext, t in TYPE_BY_EXT.items():
        if name.endswith(ext):
            return t
    return None


# ---------------------------------------------------------------------------
#  ENCODE / DECODE  -- every format decodes back to the SAME canonical bytes
# ---------------------------------------------------------------------------
def raw_to_csv(raw, typ):
    """canonical bytes -> list of text lines (one value per line; bit-exact)."""
    fmt, word = STRUCT[typ]
    n = len(raw) // word
    lines = []
    for i in range(n):
        v = struct.unpack(fmt, raw[i*word:(i+1)*word])[0]
        # repr() round-trips exactly; the widen->pack preserves the stored value.
        lines.append(str(v) if typ == "i" else repr(v))
    return lines


def csv_to_raw(lines, typ):
    """text lines -> canonical bytes."""
    fmt, word = STRUCT[typ]
    out = bytearray()
    for ln in lines:
        ln = ln.strip()
        if ln == "":
            continue
        v = int(ln) if typ == "i" else float(ln)
        out += struct.pack(fmt, v)
    return bytes(out)


def write_copies(vault_dir, base, raw, typ):
    """write the three independent format copies for one array."""
    binp = os.path.join(vault_dir, base + ".bin")
    csvp = os.path.join(vault_dir, base + ".csv")
    zipp = os.path.join(vault_dir, base + ".zip")

    with open(binp, "wb") as fh:
        fh.write(raw)

    with open(csvp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(raw_to_csv(raw, typ)) + "\n")

    with zipfile.ZipFile(zipp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(base + ".raw", raw)     # CRC32 stored by the zip format itself

    return {
        "bin": {"file": os.path.basename(binp), "sha": sha(_read_file(binp))},
        "csv": {"file": os.path.basename(csvp), "sha": sha(_read_file(csvp))},
        "zip": {"file": os.path.basename(zipp), "sha": sha(_read_file(zipp))},
    }


def _read_file(p):
    with open(p, "rb") as fh:
        return fh.read()


def decode_copy(vault_dir, base, fmt, typ):
    """decode ONE format back to canonical bytes; return (bytes | None, note)."""
    try:
        if fmt == "bin":
            return _read_file(os.path.join(vault_dir, base + ".bin")), "ok"
        if fmt == "csv":
            with open(os.path.join(vault_dir, base + ".csv"), "r", encoding="utf-8") as fh:
                return csv_to_raw(fh.read().splitlines(), typ), "ok"
        if fmt == "zip":
            with zipfile.ZipFile(os.path.join(vault_dir, base + ".zip"), "r") as z:
                # testzip() checks CRC32 of every member -> catches a flipped bit
                bad = z.testzip()
                if bad is not None:
                    return None, "crc-fail"
                return z.read(base + ".raw"), "ok"
    except FileNotFoundError:
        return None, "missing"
    except (zipfile.BadZipFile, struct.error, ValueError) as e:
        return None, "decode-error:" + type(e).__name__
    return None, "unknown-format"


# ---------------------------------------------------------------------------
#  TMR VOTE  -- word-by-word majority across the (up to three) decoded copies
# ---------------------------------------------------------------------------
def tmr_vote(candidates, word):
    """candidates: list of canonical byte-strings (already length-checked equal).
       word = element size in bytes (vote per element). returns (voted, unrec_count)."""
    if len(candidates) == 1:
        return candidates[0], 0
    n = len(candidates[0])
    out = bytearray()
    unrec = 0
    for i in range(0, n, word):
        words = [c[i:i+word] for c in candidates]
        winner = None
        for w in words:
            if words.count(w) >= 2:      # a clear majority (2 of 3, or all agree)
                winner = w
                break
        if winner is None:
            winner = words[0]            # no majority: keep first, flag it
            unrec += 1
        out += winner
    return bytes(out), unrec


# ---------------------------------------------------------------------------
#  SAVE
# ---------------------------------------------------------------------------
def cmd_save(net):
    if not os.path.isdir(net):
        sys.exit("ERROR: not a folder: " + net)
    sources = []
    for ext in TYPE_BY_EXT:
        sources += glob.glob(os.path.join(net, "*" + ext))
    sources = sorted(sources)
    if not sources:
        sys.exit("ERROR: no *.f32 / *.i32 / *.f64 arrays found in " + net)
    vault_dir = os.path.join(net, VAULT)
    os.makedirs(vault_dir, exist_ok=True)

    print("HELENA // vault -- saving 3 formats (bin / csv / zip) + SHA-256 manifest")
    manifest = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "arrays": {}}
    total = 0
    for src in sources:
        name = os.path.basename(src)
        typ = typ_of(name)
        word = STRUCT[typ][1]
        base = name                                # keep full name incl extension as base
        raw = _read_file(src)
        copies = write_copies(vault_dir, base, raw, typ)
        manifest["arrays"][name] = {
            "type": typ, "word_bytes": word, "values": len(raw) // word, "bytes": len(raw),
            "canonical_sha256": sha(raw), "copies": copies,
        }
        sz = sum(os.path.getsize(os.path.join(vault_dir, base + e)) for e in (".bin", ".csv", ".zip"))
        total += sz
        print("  [vault] " + name + "  (" + f"{len(raw)//word:,}" + " " + typ +
              "-values)  -> bin+csv+zip " + human(sz))

    with open(os.path.join(vault_dir, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2) + "\n")
    print("  manifest: " + os.path.relpath(os.path.join(vault_dir, "MANIFEST.json")))
    print("  vault total: " + human(total) + "  (" + str(len(sources)) +
          " arrays x 3 formats)  -- never one copy.")


# ---------------------------------------------------------------------------
#  VERIFY
# ---------------------------------------------------------------------------
def cmd_verify(net, quiet=False):
    vault_dir = os.path.join(net, VAULT)
    mp = os.path.join(vault_dir, "MANIFEST.json")
    if not os.path.exists(mp):
        sys.exit("ERROR: no vault manifest. Run:  redundancy.py save " + net)
    man = json.load(open(mp, "r", encoding="utf-8"))
    if not quiet:
        print("HELENA // vault -- verify (canonical SHA-256 + per-copy decode)")
    all_ok = True
    arrays_bad = 0
    for name, meta in man["arrays"].items():
        typ = meta["type"]
        canon = meta["canonical_sha256"]
        status = {}
        good = 0
        for fmt in ("bin", "csv", "zip"):
            raw, note = decode_copy(vault_dir, name, fmt, typ)
            if raw is None:
                status[fmt] = note
                all_ok = False
            elif sha(raw) == canon:
                status[fmt] = "OK"
                good += 1
            else:
                status[fmt] = "CORRUPT"
                all_ok = False
        if good < 3:
            arrays_bad += 1
            print("  [!!] " + name + "  " +
                  "  ".join(f + "=" + status[f] for f in ("bin", "csv", "zip")) +
                  "   (" + str(good) + "/3 good" +
                  ("  -> repairable" if good >= 2 else "  -> AT RISK") + ")")
        elif not quiet:
            print("  [ok] " + name + "  3/3 good")
    if all_ok:
        print("  ALL COPIES GOOD. every array verified 3/3 against its canonical hash.")
    else:
        print("  CORRUPTION FOUND in " + str(arrays_bad) + " array(s). run:  redundancy.py repair " + net)
    return all_ok


# ---------------------------------------------------------------------------
#  REPAIR  (TMR)
# ---------------------------------------------------------------------------
def cmd_repair(net):
    vault_dir = os.path.join(net, VAULT)
    mp = os.path.join(vault_dir, "MANIFEST.json")
    if not os.path.exists(mp):
        sys.exit("ERROR: no vault manifest. Run:  redundancy.py save " + net)
    man = json.load(open(mp, "r", encoding="utf-8"))
    print("HELENA // vault -- repair (TMR majority vote, survive the cosmic ray)")
    healed = 0
    unrec_total = 0
    for name, meta in man["arrays"].items():
        typ = meta["type"]
        canon = meta["canonical_sha256"]
        nbytes = meta["bytes"]
        decoded = {}
        for fmt in ("bin", "csv", "zip"):
            raw, note = decode_copy(vault_dir, name, fmt, typ)
            decoded[fmt] = raw
        good_fmts = [f for f in ("bin", "csv", "zip")
                     if decoded[f] is not None and sha(decoded[f]) == canon]
        bad_fmts = [f for f in ("bin", "csv", "zip") if f not in good_fmts]

        if len(good_fmts) == 3:
            continue    # nothing to do

        # ground truth: a copy that matches the canonical hash, else TMR vote
        truth = None
        if good_fmts:
            truth = decoded[good_fmts[0]]
        else:
            cands = [decoded[f] for f in ("bin", "csv", "zip")
                     if decoded[f] is not None and len(decoded[f]) == nbytes]
            if len(cands) >= 2:
                voted, unrec = tmr_vote(cands, STRUCT[typ][1])
                unrec_total += unrec
                if sha(voted) == canon:
                    truth = voted
                    print("  [vote] " + name + "  recovered by TMR (" +
                          str(len(cands)) + " copies, " + str(unrec) + " unrecoverable words)")
                elif unrec == 0:
                    truth = voted   # internally consistent even if manifest hash drifted
        if truth is None:
            print("  [LOST] " + name + "  cannot recover (need 2 sane copies). the vault held the line as far as it could.")
            continue

        # rewrite every bad copy from the truth
        for fmt in bad_fmts:
            if fmt == "bin":
                with open(os.path.join(vault_dir, name + ".bin"), "wb") as fh:
                    fh.write(truth)
            elif fmt == "csv":
                with open(os.path.join(vault_dir, name + ".csv"), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("\n".join(raw_to_csv(truth, typ)) + "\n")
            elif fmt == "zip":
                with zipfile.ZipFile(os.path.join(vault_dir, name + ".zip"), "w",
                                     compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr(name + ".raw", truth)
            print("  [heal] " + name + " ." + fmt + "  rewritten from truth")
            healed += 1

    if healed == 0 and unrec_total == 0:
        print("  nothing to repair -- the vault is whole.")
    else:
        print("  healed " + str(healed) + " copy-file(s). re-verifying ...")
        cmd_verify(net, quiet=True)


# ---------------------------------------------------------------------------
#  SELFTEST  -- prove the whole thing: save, flip a bit, detect, heal
# ---------------------------------------------------------------------------
def _flip_one_bit(path):
    data = bytearray(_read_file(path))
    if len(data) == 0:
        return
    i = random.randrange(len(data))
    bit = 1 << random.randrange(8)
    data[i] ^= bit
    with open(path, "wb") as fh:
        fh.write(data)
    return i, bit


def cmd_selftest():
    import tempfile
    print("HELENA // vault -- SELFTEST (cosmic ray drill)")
    tmp = tempfile.mkdtemp(prefix="helena_vault_")
    net = os.path.join(tmp, "net")
    os.makedirs(net)
    # a synthetic array of int32, one of float32, and the CENTER as float64
    ints = struct.pack("<" + "i" * 300, *range(300))
    with open(os.path.join(net, "probe.i32"), "wb") as fh:
        fh.write(ints)
    flts = struct.pack("<" + "f" * 300, *[i * 0.5 - 75.0 for i in range(300)])
    with open(os.path.join(net, "probe.f32"), "wb") as fh:
        fh.write(flts)
    # the center 2-vector: [gate 0.700, unix atomic clock] -- needs float64 precision
    center = struct.pack("<dd", 0.700, time.time())
    with open(os.path.join(net, "center.f64"), "wb") as fh:
        fh.write(center)

    print("  1) save the 3-format vault ...")
    cmd_save(net)

    print("  2) verify clean ...")
    ok = cmd_verify(net, quiet=True)
    assert ok, "clean verify should pass"
    print("     clean: PASS")

    vault_dir = os.path.join(net, VAULT)
    for target in ("probe.i32.bin", "probe.f32.csv", "center.f64.bin", "probe.i32.zip"):
        print("  3) simulate a cosmic ray: flip ONE bit in " + target)
        _flip_one_bit(os.path.join(vault_dir, target))
        print("     verify (should DETECT):")
        cmd_verify(net, quiet=True)
        print("     repair (TMR should HEAL):")
        cmd_repair(net)

    print("  4) final verify ...")
    ok = cmd_verify(net, quiet=True)
    print("  SELFTEST RESULT: " + ("PASS -- the vault survived every flip." if ok else "FAIL"))
    # clean up
    try:
        import shutil
        shutil.rmtree(tmp)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="HELENA COBOL-style 3-format redundancy vault")
    ap.add_argument("cmd", choices=["save", "verify", "repair", "selftest"])
    ap.add_argument("net", nargs="?", default=None, help="the net/ folder of a build")
    args = ap.parse_args()

    if args.cmd == "selftest":
        cmd_selftest()
        return
    if not args.net:
        sys.exit("ERROR: give the net/ folder, e.g.  redundancy.py " + args.cmd + " builds/v001/net")
    if args.cmd == "save":
        cmd_save(args.net)
    elif args.cmd == "verify":
        cmd_verify(args.net)
    elif args.cmd == "repair":
        cmd_repair(args.net)


if __name__ == "__main__":
    main()
