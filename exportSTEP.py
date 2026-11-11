import sys
import os
import FreeCAD
import Import

# FreeCAD passes its own arguments, so we take ours from the end of the list
if len(sys.argv) < 4:
    print("Usage: freecad -c exportSTEP.py <input_fcstd> <output_step>")
    sys.exit(1)

input_fcstd = sys.argv[-2]
output_step = sys.argv[-1]

if not os.path.exists(input_fcstd):
    print(f"Input FreeCAD file does not exist: {input_fcstd}")
    sys.exit(1)

# Open the FreeCAD file
doc = FreeCAD.openDocument(input_fcstd)

# Gather every object that carries a shape (Part features, PartDesign bodies, etc.)
objects = [obj for obj in doc.Objects if hasattr(obj, "Shape") and not obj.Shape.isNull()]

if not objects:
    print("No objects with shapes found in the document")
    sys.exit(1)

# Export to STEP (keeps exact BRep geometry, colors and object placements)
Import.export(objects, output_step)

print(f"STEP file exported successfully: {output_step}")

# Close the document
FreeCAD.closeDocument(doc.Name)

sys.exit(0)
