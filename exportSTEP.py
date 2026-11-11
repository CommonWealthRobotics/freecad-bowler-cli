import sys
import os
import re
import FreeCAD
import Import
import MeshPart

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

# Gather top-level objects that carry a shape (Part features, PartDesign
# bodies, etc.). Skipping children (e.g. the Pad/Sketch features inside a
# PartDesign::Body) avoids exporting the same geometry multiple times.
children = set()
for obj in doc.Objects:
    for child in getattr(obj, "Group", []):
        children.add(child.Name)

objects = [
    obj
    for obj in doc.Objects
    if obj.Name not in children and hasattr(obj, "Shape") and not obj.Shape.isNull()
]

if not objects:
    print("No objects with shapes found in the document")
    sys.exit(1)

# Export to STEP (keeps exact BRep geometry, colors and object placements)
Import.export(objects, output_step)


# FreeCAD's writer does not carry a tessellation, so a reader would have to
# triangulate each BRep face on its own and the seams between curved faces
# come out as T-joints, which no mesh kernel accepts as a solid. Attach the
# same welded mesh the STL export produces to every BRep representation, the
# way AP242 pairs a tessellation with the topology it belongs to.
def add_tessellations(path, shapes):
    with open(path, "r") as f:
        text = f.read()

    # the BRep representations, in the order the objects were exported
    brep_reps = re.findall(r"#(\d+)\s*=\s*ADVANCED_BREP_SHAPE_REPRESENTATION\(", text)
    if len(brep_reps) != len(shapes):
        print(
            f"Cannot attach tessellations: {len(brep_reps)} BRep representations "
            f"for {len(shapes)} objects"
        )
        return

    def fmt(value):
        # shortest round-trippable form
        text = repr(float(value))
        return text

    additions = []
    next_id = max(int(n) for n in re.findall(r"#(\d+)\s*=", text)) + 1

    def add(entity):
        nonlocal next_id
        ref = next_id
        next_id += 1
        additions.append(f"#{ref}={entity};")
        return ref

    for brep, obj in zip(brep_reps, shapes):
        # the context the BRep representation itself uses
        match = re.search(
            r"#" + brep + r"\s*=\s*ADVANCED_BREP_SHAPE_REPRESENTATION\('[^']*',\([^)]*\),#(\d+)\)",
            text,
        )
        if not match:
            print(f"No context found for BRep representation #{brep}")
            continue
        context = match.group(1)

        mesh = MeshPart.meshFromShape(
            obj.Shape, LinearDeflection=0.1, AngularDeflection=0.523599
        )
        points, facets = mesh.Topology
        if not facets:
            continue

        coordinate_refs = ",".join(
            "#" + str(add(f"CARTESIAN_POINT('',({fmt(p.x)},{fmt(p.y)},{fmt(p.z)}))"))
            for p in points
        )
        coordinates = add(
            f"COORDINATES_LIST('',{len(points)},({coordinate_refs}))"
        )
        triangles = ",".join(
            "(%d,%d,%d)" % tuple(int(i) + 1 for i in facet) for facet in facets
        )
        surface = add(
            f"TRIANGULATED_SURFACE_SET('mesh',#{coordinates},{len(points)},$,$,$,({triangles}))"
        )

        origin = add("CARTESIAN_POINT('',(0.,0.,0.))")
        axis = add("DIRECTION('',(0.,0.,1.))")
        reference = add("DIRECTION('',(1.,0.,0.))")
        placement = add(
            f"AXIS2_PLACEMENT_3D('',#{origin},#{axis},#{reference})"
        )
        tessellated = add(
            f"TESSELLATED_SHAPE_REPRESENTATION('{obj.Name}',(#{placement},#{surface}),#{context})"
        )
        # the tessellation describes the same shape, at the same coordinates
        add(
            f"SHAPE_REPRESENTATION_RELATIONSHIP('{obj.Name}','tessellation of the BRep',"
            f"#{brep},#{tessellated})"
        )

    with open(path, "a") as f:
        f.write("\n".join(additions) + "\n")


add_tessellations(output_step, objects)

print(f"STEP file exported successfully: {output_step}")

# Close the document
FreeCAD.closeDocument(doc.Name)

sys.exit(0)
