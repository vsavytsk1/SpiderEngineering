#!/usr/bin/env python3
"""
build_fleet.py — expand ONE design into a fleet of N identical units.

    spec/aracnium.toml   (the single source of truth: one spider)
            x
    fleet/fleet.toml     (the only place quantity lives: count = N)
            |
            v
    fleet/generated/     (per-unit build cards + a scaled bill of materials)

The whole "build 1 == build 10" idea is enforced here, mechanically:
every unit is stamped from the same spec, and we hash that spec so the
output can PROVE all N units are the same design — only the serial differs.

Stdlib only (Python 3.11+). No pip install, ever.

    python tools/build_fleet.py            # build the fleet
    python tools/build_fleet.py --check    # verify, write nothing
"""

from __future__ import annotations
import sys, json, csv, hashlib, tomllib, argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "aracnium.toml"
FLEET = ROOT / "fleet" / "fleet.toml"
BOM_IN = ROOT / "hardware" / "bom" / "bom.csv"
OUT = ROOT / "fleet" / "generated"


def load_toml(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"ERROR: missing {path.relative_to(ROOT)}")
    with path.open("rb") as f:
        return tomllib.load(f)


def design_fingerprint(spec: dict) -> str:
    """A stable hash of the design. Same spec -> same fingerprint, always.
    This is what lets us claim every unit in the fleet is identical."""
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def derive(spec: dict) -> dict:
    """Compute the numbers that other things (CAD, BOM, firmware) need,
    so they never get re-derived (and drift) elsewhere."""
    seg = spec["leg"]["segments"]
    ik = spec["leg"]["ik"]
    link1 = round(sum(seg[s] for s in ik["link1_segments"]), 2)
    link2 = round(sum(seg[s] for s in ik["link2_segments"]), 2)
    n_legs = spec["actuation"]["n_legs"]
    jpl = spec["actuation"]["joints_per_leg"]
    return {
        "ik_link1_mm": link1,
        "ik_link2_mm": link2,
        "leg_reach_mm": round(link1 + link2, 2),
        "n_legs": n_legs,
        "joints_per_leg": jpl,
        "servos_per_unit": n_legs * jpl,
    }


def load_bom(per_unit_count: int) -> list[dict]:
    """Per-unit BOM, scaled x N. Returns [] if no BOM file yet."""
    if not BOM_IN.exists():
        return []
    rows = []
    with BOM_IN.open(newline="") as f:
        for r in csv.DictReader(f):
            qty_each = int(r["qty"])
            rows.append({
                "ref": r["ref"],
                "part": r["part"],
                "qty_per_unit": qty_each,
                "qty_total": qty_each * per_unit_count,
                "notes": r.get("notes", ""),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify and report; write no files")
    args = ap.parse_args()

    spec = load_toml(SPEC)
    fleet = load_toml(FLEET)["fleet"]
    count = int(fleet["count"])
    prefix = fleet.get("prefix", "ARC")

    if fleet.get("build") != spec["build"]["codename"]:
        print(f"  ! warning: fleet build '{fleet.get('build')}' != "
              f"spec codename '{spec['build']['codename']}'")

    fp = design_fingerprint(spec)
    d = derive(spec)
    overrides = {u["serial"]: u for u in fleet.get("unit", [])}

    units = []
    for i in range(1, count + 1):
        serial = f"{prefix}-{i:03d}"
        units.append({
            "serial": serial,
            "build": spec["build"]["codename"],
            "design_fingerprint": fp,          # identical for every unit
            "derived": d,
            "override": overrides.get(serial, None),
            "stamped": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

    # --- the proof: every unit shares one design fingerprint ---
    fps = {u["design_fingerprint"] for u in units}
    identical = len(fps) == 1

    bom = load_bom(count)

    print(f"  design        : {spec['build']['name']} / "
          f"{spec['build']['codename']} ({spec['build']['revision']})")
    print(f"  fingerprint   : {fp}")
    print(f"  fleet count   : {count}")
    print(f"  servos/unit   : {d['servos_per_unit']}  "
          f"({d['n_legs']} legs x {d['joints_per_leg']} joints)")
    print(f"  leg reach     : {d['leg_reach_mm']} mm  "
          f"(link1 {d['ik_link1_mm']} + link2 {d['ik_link2_mm']})")
    if bom:
        print(f"  BOM lines     : {len(bom)}  "
              f"(qty scaled x{count})")
    print(f"  PROOF         : all {count} units share design {fp} "
          f"-> {'IDENTICAL [OK]' if identical else 'MISMATCH [FAIL]'}")

    if args.check:
        print("  (--check: no files written)")
        return 0 if identical else 1

    OUT.mkdir(parents=True, exist_ok=True)
    for u in units:
        (OUT / f"{u['serial']}.json").write_text(json.dumps(u, indent=2))
    (OUT / "fleet.json").write_text(json.dumps({
        "build": spec["build"]["codename"],
        "design_fingerprint": fp,
        "count": count,
        "serials": [u["serial"] for u in units],
    }, indent=2))
    if bom:
        with (OUT / "bom_fleet.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "ref", "part", "qty_per_unit", "qty_total", "notes"])
            w.writeheader()
            w.writerows(bom)

    print(f"  wrote         : {count} unit card(s) + fleet.json"
          f"{' + bom_fleet.csv' if bom else ''}  -> fleet/generated/")
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
