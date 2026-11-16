"""Counts the solids each Part feature of a FreeCAD document carries.

Usage:
    freecad -c count_solids.py <document.fcstd> <report.json>
    FCSTD_FILE=document.fcstd SOLIDS_REPORT=report.json freecadcmd -c count_solids.py

Writes {"solids": <n>, "shells": <n>, "compounds": <n>} for a caller that
loads the verdict rather than reading a log: the STEP correction loop treats
a document whose features carry no solid as a STEP that came apart in the
import, and corrects the mesh before writing the file again.
"""

import json
import os
import sys
import time
import traceback

import FreeCAD
import Part


def finish(code):
    # FreeCAD drops into an interactive console after a script returns, and
    # that console reads a stdin that never ends on Windows CI; the only exit
    # that cannot hang is a hard one
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run():
    # the paths arrive either as the last two command-line arguments (the same way
    # importSTEP.py takes them, which works under every launcher) or as environment
    # variables for a freecadcmd caller, whose launcher imports trailing file
    # arguments as documents
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) >= 2:
        document, report = args[-2], args[-1]
    elif "FCSTD_FILE" in os.environ and "SOLIDS_REPORT" in os.environ:
        document = os.environ["FCSTD_FILE"]
        report = os.environ["SOLIDS_REPORT"]
    else:
        raise SystemExit(
            "usage: freecad -c count_solids.py <document.fcstd> <report.json>"
            " (or set FCSTD_FILE and SOLIDS_REPORT)")

    doc = FreeCAD.openDocument(document)
    solids = 0
    shells = 0
    compounds = 0
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        solids += len(shape.Solids)
        shells += len(shape.Shells)
        if shape.ShapeType == "Compound":
            compounds += 1

    with open(report, "w") as out:
        json.dump({"solids": solids, "shells": shells, "compounds": compounds}, out)
    print("GATE-COUNT solids=%d shells=%d compounds=%d report=%s" % (solids, shells, compounds, report))
    finish(0)


try:
    run()
except BaseException:
    traceback.print_exc()
    time.sleep(0.2)  # let the log drain before the hard exit
    finish(1)
