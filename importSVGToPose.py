import sys
import os
import traceback
import FreeCAD
import importSVG
import Part
import Sketcher

log_file = open('freecad_script.log', 'w')

def log_print(message, error=False):
    if error:
        FreeCAD.Console.PrintError(f"{message}\n")
    else:
        FreeCAD.Console.PrintMessage(f"{message}\n")
    log_file.write(f"{message}\n")
    log_file.flush()

log_print("Script started")
log_print(f"Number of arguments: {len(sys.argv)}")
log_print(f"Arguments: {sys.argv}")

def parse_vector(vector_str):
    try:
        return FreeCAD.Vector(*map(float, vector_str.strip('\'"').split(',')))
    except ValueError as e:
        log_print(f"Error parsing vector: {vector_str.strip('\'"')}", error=True)
        raise e

def parse_quaternion(quat_str):
    try:
        return FreeCAD.Rotation(*map(float, quat_str.strip('\'"').split(',')))
    except ValueError as e:
        log_print(f"Error parsing quaternion: {quat_str.strip('\'"')}", error=True)
        raise e

try:
    log_print("Checking arguments")
    if len(sys.argv) < 7:
        raise ValueError(f"Not enough arguments. Usage: <input_fcstd> <input_svg> <position> <quaternion>. Got: {sys.argv}")

    input_fcstd = sys.argv[-4]
    input_svg = sys.argv[-3]
    position_str = sys.argv[-2]
    quaternion_str = sys.argv[-1]

    log_print(f"Input FreeCAD file: {input_fcstd}")
    log_print(f"Input SVG file: {input_svg}")
    log_print(f"Position string: {position_str}")
    log_print(f"Quaternion string: {quaternion_str}")

    position = parse_vector(position_str)
    quaternion = parse_quaternion(quaternion_str)

    log_print(f"Parsed position: {position}")
    log_print(f"Parsed quaternion: {quaternion}")

    
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

except BaseException as e:
    log_print(f"An error occurred: {str(e)}", error=True)
    log_print("Traceback:", error=True)
    log_print(traceback.format_exc(), error=True)
    sys.exit(1)

log_print("Script ended")
log_file.close()
sys.exit(0)