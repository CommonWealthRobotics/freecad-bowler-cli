import sys
import os
import traceback
import FreeCAD
import importSVG
import Part
import Sketcher

# Open a log file
log_file = open('freecad_script.log', 'w')

def log_print(message, error=False):
    if error:
        FreeCAD.Console.PrintError(f"{message}\n")
    else:
        FreeCAD.Console.PrintMessage(f"{message}\n")
    log_file.write(f"{message}\n")
    log_file.flush()

log_print("Script started")

def parse_vector(vector_str):
    return FreeCAD.Vector(*map(float, vector_str.split(',')))

def parse_quaternion(quat_str):
    return FreeCAD.Rotation(*map(float, quat_str.split(',')))

try:
    log_print("Checking arguments")
    if len(sys.argv) < 5:
        raise ValueError("Usage: <input_fcstd> <input_svg> <position> <quaternion>")

    input_fcstd = sys.argv[1]
    input_svg = sys.argv[2]
    position = parse_vector(sys.argv[3])
    quaternion = parse_quaternion(sys.argv[4])

    log_print(f"Opening FreeCAD file: {input_fcstd}")
    doc = FreeCAD.open(input_fcstd)

    log_print("Creating reference frame")
    ref_frame = doc.addObject('Part::Feature', 'ReferenceFrame')
    ref_frame.Placement = FreeCAD.Placement(position, quaternion)

    log_print(f"Importing SVG: {input_svg}")
    imported_objects = importSVG.insert(input_svg, doc.Name)
    log_print(f"Imported {len(imported_objects)} objects from SVG")

    for i, obj in enumerate(imported_objects):
        log_print(f"Processing object {i+1}/{len(imported_objects)}")
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
            
            log_print(f"  Added {edge_count} edges to sketch")
            
            log_print(f"  Removing original imported object: {obj.Name}")
            doc.removeObject(obj.Name)

    log_print("Recomputing document")
    doc.recompute()

    log_print("Checking for recompute errors")
    errors = doc.recompute(None, True)
    if errors:
        log_print("Recompute errors occurred:", error=True)
        for err in errors:
            log_print(f"  {err[0]}: {err[1]}", error=True)
    else:
        log_print("Recompute completed successfully")

    log_print(f"Saving document to: {input_fcstd}")
    doc.saveAs(input_fcstd)

    log_print("Closing document")
    FreeCAD.closeDocument(doc.Name)

    log_print("Script execution completed successfully")

except Exception as e:
    log_print(f"An error occurred: {str(e)}", error=True)
    log_print("Traceback:", error=True)
    log_print(traceback.format_exc(), error=True)

log_print("Script ended")

# Close the log file
log_file.close()