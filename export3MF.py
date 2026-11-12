import sys
import os
import FreeCAD
import Mesh

# FreeCAD passes its own arguments, so we take ours from the end of the list
if len(sys.argv) < 4:
    print("Usage: freecad -c export3MF.py <input_fcstd> <output_3mf>")
    sys.exit(1)

input_fcstd = sys.argv[-2]
output_3mf = sys.argv[-1]

if not os.path.exists(input_fcstd):
    print(f"Input FreeCAD file does not exist: {input_fcstd}")
    sys.exit(1)

doc = FreeCAD.openDocument(input_fcstd)

# Top-level objects carrying a solid shape. Skipping children of groups/bodies
# avoids exporting the same geometry twice; skipping non-solids keeps sketches out.
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
    sys.exit(1)

# Tessellation tolerance used by the exporter (same default as your 0.1 mm)
FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Mesh").SetFloat(
    "MaxDeviationExport", 0.0001
)

# Built-in export: format chosen by the .3mf extension
Mesh.export(solids, output_3mf)

print(f"3MF file exported successfully: {output_3mf} ({len(solids)} object(s))")

FreeCAD.closeDocument(doc.Name)
sys.exit(0)