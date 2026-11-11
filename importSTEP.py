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

# Snapshot so we can tell the importer's objects from ours afterwards
objects_before = set(doc.Objects)

# Import the STEP file into the active document; the importer creates one
# Part::Feature per solid, grouped under an App::Part container named after
# the source file.
Import.insert(input_step, doc.Name)

doc.recompute()

imported_objects = [obj for obj in doc.Objects if obj not in objects_before]

# Collect every imported solid and re-home it under our own named feature so
# the caller can address the result by object_name
shape_list = []
for obj in imported_objects:
    if obj.TypeId == "App::Part":
        continue  # container: its shape would duplicate the child features
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shape_list.extend(obj.Shape.Solids)

if not shape_list:
    print(f"STEP import failed: no solids found in {input_step}")
    sys.exit(1)

for i, shape in enumerate(shape_list):
    name = object_name if len(shape_list) == 1 else f"{object_name}_{i}"
    new_object = doc.addObject("Part::Feature", name)
    new_object.Shape = shape

# Remove everything the importer created, keeping only our named features;
# removing a container deletes its children (origin planes/axes) with it
for obj in imported_objects:
    try:
        name = obj.Name
    except ReferenceError:
        continue  # already deleted as a child of an earlier removal
    if doc.getObject(name) is not None:
        doc.removeObject(name)

doc.recompute()

# Save the document
doc.saveAs(output_fcstd)

print(f"STEP imported and saved to: {output_fcstd}")

# Close the document
FreeCAD.closeDocument(doc.Name)

# Exit the script
sys.exit(0)
