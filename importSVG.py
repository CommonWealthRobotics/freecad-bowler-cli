import sys
import os
import traceback
import FreeCAD
import importSVG
import Part
import Sketcher

def fc_print(message):
    FreeCAD.Console.PrintMessage(f"{message}\n")

fc_print("Script started")

def parse_vector(vector_str):
    return FreeCAD.Vector(*map(float, vector_str.split(',')))

def parse_quaternion(quat_str):
    return FreeCAD.Rotation(*map(float, quat_str.split(',')))

try:
    fc_print("Checking arguments")
    if len(sys.argv) < 5:
        raise ValueError("Usage: <input_fcstd> <input_svg> <position> <quaternion>")

    input_fcstd = sys.argv[1]
    input_svg = sys.argv[2]
    position = parse_vector(sys.argv[3])
    quaternion = parse_quaternion(sys.argv[4])

    fc_print(f"Opening FreeCAD file: {input_fcstd}")
    doc = FreeCAD.open(input_fcstd)

    fc_print("Creating reference frame")
    ref_frame = doc.addObject('Part::Feature', 'ReferenceFrame')
    ref_frame.Placement = FreeCAD.Placement(position, quaternion)

    fc_print(f"Importing SVG: {input_svg}")
    imported_objects = importSVG.insert(input_svg, doc.Name)
    fc_print(f"Imported {len(imported_objects)} objects from SVG")

    for i, obj in enumerate(imported_objects):
        fc_print(f"Processing object {i+1}/{len(imported_objects)}")
        if hasattr(obj, 'Shape'):
            sketch = doc.addObject('Sketcher::SketchObject', f'SVGSketch_{i+1}')
            sketch.Placement = ref_frame.Placement
            
            edge_count = 0
            for edge in obj.Shape.Edges:
                if isinstance(edge.Curve, Part.Line):
                    sketch.addGeometry(Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[1].Point))
                    edge_count += 1
                elif isinstance(edge.Curve, Part.Circle):
                    sketch.addGeometry(Part.Circle(edge.Curve.Center, edge.Curve.Axis, edge.Curve.Radius))
                    edge_count += 1
            
            fc_print(f"  Added {edge_count} edges to sketch")
            
            fc_print(f"  Removing original imported object: {obj.Name}")
            doc.removeObject(obj.Name)

    fc_print("Recomputing document")
    #doc.recompute()

    fc_print("Checking for recompute errors")
    #errors = doc.recompute(None, True)
    if errors:
        FreeCAD.Console.PrintError("Recompute errors occurred:\n")
        for err in errors:
            FreeCAD.Console.PrintError(f"  {err[0]}: {err[1]}\n")
    else:
        fc_print("Recompute completed successfully")

    fc_print(f"Saving document to: {input_fcstd}")
    doc.saveAs(input_fcstd)

    fc_print("Closing document")
    FreeCAD.closeDocument(doc.Name)

    fc_print("Script execution completed successfully")

except Exception as e:
    FreeCAD.Console.PrintError(f"An error occurred: {str(e)}\n")
    FreeCAD.Console.PrintError("Traceback:\n")
    FreeCAD.Console.PrintError(traceback.format_exc())

fc_print("Script ended")
sys.exit(0)