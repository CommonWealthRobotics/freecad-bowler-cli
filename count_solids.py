"""Counts the solids each Part feature of a FreeCAD document carries.

Usage:
    FCSTD_FILE=document.fcstd SOLIDS_REPORT=report.json freecadcmd -c count_solids.py

Writes {"solids": <n>, "shells": <n>, "compounds": <n>} for a caller that
loads the verdict rather than reading a log: the STEP correction loop treats
a document whose features carry no solid as a STEP that came apart in the
import, and corrects the mesh before writing the file again.
"""

import json
import os
import sys

import FreeCAD
import Part

# the caller passes the paths as environment variables: freecadcmd treats
# trailing file arguments as documents to import, which a JSON report is not
document = os.environ["FCSTD_FILE"]
report = os.environ["SOLIDS_REPORT"]

doc = FreeCAD.openDocument(document)
solids = 0
shells = 0
compounds = 0
for obj in doc.Objects:
    shape = getattr(obj, "Shape", None)
    if shape is None:
        continue
    solids += len(shape.Solids)
    shells += len(shape.Shells)
    if shape.ShapeType == "Compound":
        compounds += 1

with open(report, "w") as out:
    json.dump({"solids": solids, "shells": shells, "compounds": compounds}, out)
print("GATE-COUNT solids=%d shells=%d compounds=%d report=%s" % (solids, shells, compounds, report))
