import os
import sys
import time
import traceback

import FreeCAD
import Mesh
import MeshPart


def finish(code):
    # FreeCAD drops into an interactive console after a script returns, and
    # that console reads a stdin that never ends on Windows CI; the only exit
    # that cannot hang is a hard one
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run():
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 5:
        print("Usage: freecad export_stl.py <input_file.FCStd> <output_file.stl>")
        finish(1)

    # Get input and output file paths from command line arguments
    input_file = sys.argv[3]
    output_file = sys.argv[4]

    # Open the FreeCAD file
    doc = FreeCAD.open(input_file)

    # Create a unified mesh from the top-level solid objects. Skipping children
    # (e.g. the Pad/Sketch features inside a PartDesign::Body) avoids exporting
    # the same geometry multiple times, which breaks the mesh when merged.
    children = set()
    for obj in doc.Objects:
        for child in getattr(obj, "Group", []):
            children.add(child.Name)

    meshes = []
    for obj in doc.Objects:
        if obj.Name in children:
            continue
        if hasattr(obj, "Shape"):
            if not obj.Shape.Solids:
                continue  # sketches and other non-solid shapes cannot be meshed
            # Convert shape to mesh with reasonable precision
            mesh = MeshPart.meshFromShape(obj.Shape, LinearDeflection=0.1, AngularDeflection=0.523599)
            meshes.append(mesh)

    if meshes:
        # Combine all meshes
        combined_mesh = meshes[0]
        for mesh in meshes[1:]:
            combined_mesh.addMesh(mesh)

        # Remove duplicate points and faces
        combined_mesh.removeDuplicatedPoints()
        combined_mesh.removeDuplicatedFacets()

        # Optionally fix other mesh issues
        combined_mesh.removeNonManifolds()
        combined_mesh.fixDegenerations()

        # Write the cleaned mesh
        combined_mesh.write(output_file, "STL")
        print(f"STL file exported successfully: {output_file}")
    else:
        print("No objects with shapes found in the document")
        finish(1)

    # Close the document
    FreeCAD.closeDocument(doc.Name)

    finish(0)


try:
    run()
except BaseException:
    traceback.print_exc()
    time.sleep(0.2)  # let the log drain before the hard exit
    finish(1)
