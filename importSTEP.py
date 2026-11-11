import sys
import os
import FreeCAD
import Import

# FreeCAD passes its own arguments, so we take ours from the end of the list
if len(sys.argv) < 5:
    print("Usage: freecad -c importSTEP.py <output_fcstd> <input_step> <object_name>")
    sys.exit(1)

input_step = sys.argv[-2]
output_fcstd = sys.argv[-3]
object_name = sys.argv[-1]

if not os.path.exists(input_step):
    print(f"Input STEP file does not exist: {input_step}")
    sys.exit(1)

# Open the output_fcstd file or create a new document if it doesn't exist
if os.path.exists(output_fcstd):
    doc = FreeCAD.openDocument(output_fcstd)
else:
    doc = FreeCAD.newDocument()

FreeCAD.setActiveDocument(doc.Name)

# Import the STEP file into the active document
# (Import.insert is the GUI import command; it creates the objects for us)
imported_objects = Import.insert(input_step, doc.Name)

doc.recompute()

if not imported_objects:
    print(f"STEP import failed: no objects found in {input_step}")
    sys.exit(1)

# FreeCAD's importer makes one Part::Feature per solid, each with its own placement.
# Re-import those shapes as our own named Part::Feature objects so the caller can
# address them by name, and remove the generically-named importer objects.
shape_list = []
for obj in imported_objects:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shape_list.append(obj.Shape)

for i, shape in enumerate(shape_list):
    name = object_name if len(shape_list) == 1 else f"{object_name}_{i}"
    new_object = doc.addObject("Part::Feature", name)
    new_object.Shape = shape

for obj in imported_objects:
    doc.removeObject(obj.Name)

doc.recompute()

# Save the document
doc.saveAs(output_fcstd)

print(f"STEP imported and saved to: {output_fcstd}")

# Close the document
FreeCAD.closeDocument(doc.Name)

# Exit the script
sys.exit(0)
