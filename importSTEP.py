import sys
import os
import json
import FreeCAD
import Import

# FreeCAD passes its own arguments, so we take ours from the end of the list
if len(sys.argv) < 5:
    print("Usage: freecad -c importSTEP.py <output_fcstd> <input_step> <object_name> [colors_json]")
    sys.exit(1)

# the last argument is optionally a colours manifest, {"0": "#RRGGBB", ...},
# indexed by the order the solids appear in the STEP file
colors_json = None
if sys.argv[-1].lower().endswith(".json"):
    colors_json = sys.argv[-1]
    sys.argv = sys.argv[:-1]

input_step = sys.argv[-2]
output_fcstd = sys.argv[-3]
object_name = sys.argv[-1]

if not os.path.exists(input_step):
    print(f"Input STEP file does not exist: {input_step}")
    sys.exit(1)

colors = {}
if colors_json and os.path.exists(colors_json):
    with open(colors_json, "r") as f:
        colors = json.load(f)

def color_of(index):
    hex_color = colors.get(str(index))
    if not hex_color:
        return None
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return None
    return (
        int(hex_color[0:2], 16) / 255.0,
        int(hex_color[2:4], 16) / 255.0,
        int(hex_color[4:6], 16) / 255.0,
        1.0,
    )

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
    # headless FreeCAD has no view provider, so a solid's colour is kept in a
    # dynamic property for the 3MF export to read back
    solid_color = color_of(i)
    if solid_color:
        new_object.addProperty("App::PropertyColor", "CaDoodleColor")
        new_object.CaDoodleColor = solid_color

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
