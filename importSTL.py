import os
import sys
import time
import traceback

import FreeCAD
import Mesh
import Part


def finish(code):
    # FreeCAD drops into an interactive console after a script returns, and
    # that console reads a stdin that never ends on Windows CI; the only exit
    # that cannot hang is a hard one
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run():
    # FreeCAD passes its own arguments, so we need to adjust our index
    if len(sys.argv) < 5:
        print("Usage: freecad script.py  <output_fcstd> <input_stl> <object_name>")
        finish(1)

    input_stl = sys.argv[-2]
    output_fcstd = sys.argv[-3]
    object_name = sys.argv[-1]

    if not os.path.exists(input_stl):
        print(f"Input STL file does not exist: {input_stl}")
        finish(1)

    # Open the output_fcstd file or create a new document if it doesn't exist
    if os.path.exists(output_fcstd):
        doc = FreeCAD.openDocument(output_fcstd)
    else:
        doc = FreeCAD.newDocument()

    FreeCAD.setActiveDocument(doc.Name)

    # Import the STL file
    mesh = Mesh.Mesh(input_stl)
    mesh_object = doc.addObject("Mesh::Feature", f"{object_name}_Mesh")
    mesh_object.Mesh = mesh

    # Optional: Convert mesh to solid
    # shape = Part.Shape()
    # shape.makeShapeFromMesh(mesh.Topology, 0.1)
    # solid = Part.makeSolid(shape)
    # solid_object = doc.addObject("Part::Feature", f"{object_name}_Solid")
    # solid_object.Shape = solid

    # Recompute the document
    doc.recompute()

    # Save the document
    doc.saveAs(output_fcstd)

    print(f"STL imported and saved to: {output_fcstd}")

    # Close the document
    FreeCAD.closeDocument(doc.Name)

    # Exit the script
    finish(0)


try:
    run()
except BaseException:
    traceback.print_exc()
    time.sleep(0.2)  # let the log drain before the hard exit
    finish(1)
