#!/usr/bin/env python3
"""PrusaSlicer post-processing script: metadata only. NEVER emits machine moves.

PrusaSlicer calls post-processing scripts with the G-code filename as last arg.
Only runs when operator explicitly configures the script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

MARKER_BEGIN = '; FENCEPOST-001 METADATA BEGIN\n'
MARKER_END = '; FENCEPOST-001 METADATA END\n'


def annotate(gcode: Path, receipt: Path) -> bool:
    data=json.loads(receipt.read_text(encoding='utf-8'))
    if data.get('schema')!='fencepost-001/dry-run/v1' or data.get('status')!='HOLD_SIMULATION_ONLY' or data.get('cutting_authorized') is not False:
        raise ValueError('Only held FENCEPOST-001 dry-run receipts accepted')
    original=gcode.read_bytes()
    content=original.decode('utf-8')
    if MARKER_BEGIN.strip() in content:
        return False  # idempotent
    digest=hashlib.sha256(receipt.read_bytes()).hexdigest()
    prefix=(MARKER_BEGIN + '; SOURCE RECEIPT SHA256 '+digest+'\n'
            + '; REVERSE SEISMOGRAPH / SIMULATION ONLY / NO CUTTING AUTHORITY\n'
            + MARKER_END)
    gcode.write_bytes(prefix.encode('utf-8')+original)
    return True


def main(argv=None):
    ap=argparse.ArgumentParser(description='Read-only provenance annotation of an existing slicer G-code; no motion changes')
    ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('gcode',type=Path)
    args=ap.parse_args(argv)
    try:
        print('Annotated' if annotate(args.gcode,args.receipt) else 'Already annotated')
    except (ValueError,OSError,UnicodeError,json.JSONDecodeError) as exc:
        ap.error(str(exc))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
