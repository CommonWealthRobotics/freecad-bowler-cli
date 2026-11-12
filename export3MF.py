import sys
import os
import FreeCAD
import Mesh

def finish(code):
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

if len(sys.argv) < 4:
    print("Usage: freecad -c export3MF.py <input_fcstd> <output_3mf>")
    finish(1)

input_fcstd = sys.argv[-2]
output_3mf = sys.argv[-1]

if not os.path.exists(input_fcstd):
    print(f"Input FreeCAD file does not exist: {input_fcstd}")
    finish(1)

doc = FreeCAD.openDocument(input_fcstd)
doc.recompute()  # file was saved by an older version; refresh shapes

children = {child.Name for obj in doc.Objects for child in getattr(obj, "Group", [])}

solids = [
    obj for obj in doc.Objects
    if obj.Name not in children
    and hasattr(obj, "Shape")
    and not obj.Shape.isNull()
    and obj.Shape.Solids
]

if not solids:
    print("No objects with solid shapes found in the document")
    finish(1)

FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Mesh").SetFloat(
    "MaxDeviationExport", 0.1
)

Mesh.export(solids, output_3mf)
print(f"3MF file exported successfully: {output_3mf} ({len(solids)} object(s))")

FreeCAD.closeDocument(doc.Name)
finish(0)