import sys
import os
import traceback
import FreeCAD
import importSVG
import Part
import Sketcher
import xml.etree.ElementTree as ET
import math

log_file = open('freecad_script.log', 'w')

def log_print(message, error=False):
    FreeCAD.Console.PrintError(f"{message}\n")
    log_file.write(f"{message}\n")
    log_file.flush()
    #print(message)
def create_rotation_matrix(angle, axis):
    """Create a rotation matrix for a given angle (in degrees) around a given axis."""
    angle_rad = math.radians(angle)
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    t = 1 - c
    x, y, z = axis.normalize()
    return FreeCAD.Matrix(
        t*x*x + c,   t*x*y - z*s, t*x*z + y*s, 0,
        t*x*y + z*s, t*y*y + c,   t*y*z - x*s, 0,
        t*x*z - y*s, t*y*z + x*s, t*z*z + c,   0,
        0,           0,           0,           1
    )
log_print("Script started")
log_print(f"Number of arguments: {len(sys.argv)}")
log_print(f"Arguments: {sys.argv}")

def parse_vector(vector_str):
    try:
        return FreeCAD.Vector(*map(float, vector_str.strip('\'"').split(',')))
    except ValueError as e:
        log_print(f"Error parsing vector: {vector_str}", error=True)
        raise e

def parse_quaternion(quat_str):
    try:
        return FreeCAD.Rotation(*map(float, quat_str.strip('\'"').split(',')))
    except ValueError as e:
        log_print(f"Error parsing quaternion: {quat_str}", error=True)
        raise e

def get_svg_dimensions(svg_file):
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    width = root.get('width')
    height = root.get('height')
    
    # Convert to float and handle units if necessary
    def parse_dimension(dim):
        if dim.endswith('mm'):
            return float(dim[:-2])
        elif dim.endswith('cm'):
            return float(dim[:-2]) * 10
        elif dim.endswith('in'):
            return float(dim[:-2]) * 25.4
        else:
            return float(dim)
    
    return parse_dimension(width), parse_dimension(height)
try:
    log_print("Checking arguments")
    if len(sys.argv) < 9:
        raise ValueError(f"Not enough arguments. Usage: <input_fcstd> <input_svg> <position> <quaternion>. Got: {sys.argv}")

    input_fcstd = sys.argv[-6]
    input_svg = sys.argv[-5]
    position_str = sys.argv[-4]
    quaternion_str = sys.argv[-3]
    sliceName =  sys.argv[-2]
    bodyName =  sys.argv[-1]
    log_print(f"Input FreeCAD file: {input_fcstd}")
    log_print(f"Input SVG file: {input_svg}")
    log_print(f"Position string: {position_str}")
    log_print(f"Quaternion string: {quaternion_str}")

    position = parse_vector(position_str)
    quaternion = parse_quaternion(quaternion_str)
    # Create a rotation matrix for 180 degrees around X-axis
    log_print(f"Parsed quaternion IN : {quaternion}")
    # Apply the rotation to the quaternion
    #quaternion = quaternion.multiply(FreeCAD.Rotation(create_rotation_matrix(180, FreeCAD.Vector(0, 1, 0))))
    #quaternion = quaternion.multiply(FreeCAD.Rotation(create_rotation_matrix(180, FreeCAD.Vector(0, 0, 1))))
    log_print(f"Parsed quaternion ADJ: {quaternion}")
    log_print(f"Parsed position : {position}")

    log_print(f"Opening FreeCAD file: {input_fcstd}")
    if os.path.exists(output_fcstd):
        doc = FreeCAD.openDocument(output_fcstd)
    else:
        doc = FreeCAD.newDocument()
    FreeCAD.setActiveDocument(doc.Name)
    FreeCAD.ActiveDocument = doc

    log_print("Creating reference frame")
    ref_frame = doc.addObject('Part::Feature', 'ReferenceFrame')
    ref_frame.Placement = FreeCAD.Placement(position, quaternion)
    log_print(f"SVG file exists: {os.path.isfile(input_svg)}")
    log_print(f"SVG file size: {os.path.getsize(input_svg)} bytes")
    # After setting the reference frame so it is not deleted later
    objects_before = set(doc.Objects)
    with open(input_svg, 'r') as f:
        log_print(f"First 100 characters of SVG file: {f.read(100)}")

    log_print(f"importSVG module path: {importSVG.__file__}")
    log_print(f"importSVG.insert function: {importSVG.insert}")

    log_print(f"Importing SVG: {input_svg}")
    if not os.path.isfile(input_svg):
        log_print(f"SVG file not found: {input_svg}", error=True)
        raise ValueError(f"SVG file not found: {input_svg}")

    imported_objects = None
    try:
        if hasattr(importSVG, "importOptions"):
            log_print("Using importOptions")
            options = importSVG.importOptions(input_svg)
            options.setOption("Synchronous", True)
            imported_objects = importSVG.insert(input_svg, doc.Name, options=options)
            log_print(imported_objects)
        else:
            log_print("Not using importOptions")
            imported_objects = importSVG.insert(input_svg, doc.Name)
            log_print(imported_objects)
    except Exception as e:
        log_print(f"Exception during SVG import: {str(e)}", error=True)
        raise
    if imported_objects is None :
        log_print('WARNING: No objects returned from SVG import', error=True)
        log_print('Searching for new objects in the document')
        
        doc.recompute()
        objects_after = set(doc.Objects)
        new_objects = list(objects_after - objects_before)
        log_print(f"Found {len(new_objects)} new objects after recompute")
    
        if len(new_objects) > 0:
            imported_objects = new_objects
        else:
            log_print("No new objects found. Import may have failed.", error=True)
    log_print(f"Saving document to: {input_fcstd}")
    doc.saveAs(input_fcstd)
    svg_width, svg_height = get_svg_dimensions(input_svg)
    def apply_offset(point):
        return FreeCAD.Vector(point.x ,  point.y +svg_height , point.z)
    log_print(f"Document applying offset: ({svg_width}, {svg_height})")

    log_print(f"Imported {len(imported_objects)} objects from SVG")
    body = doc.getObject(bodyName)
    if not body:
        log_print(f"Creating new body: {bodyName}")
        body = doc.addObject('PartDesign::Body', bodyName)
    else:
        log_print(f"Using existing body: {bodyName}")
        # Create a datum plane
    datum_plane = body.newObject('PartDesign::Plane', f'DatumPlane_{sliceName}')
    datum_plane.Placement = ref_frame.Placement
    sketch = body.newObject('Sketcher::SketchObject', f'SVGSketch_{sliceName}')
    sketch.Placement = ref_frame.Placement
    for i, obj in enumerate(imported_objects):
        #log_print(f"Processing object {i+1}/{len(imported_objects)}")
        if hasattr(obj, 'Shape'):

            
            edge_count = 0
            for edge in obj.Shape.Edges:
                if isinstance(edge.Curve, Part.Line):
                    start = apply_offset(edge.Vertexes[0].Point)
                    end = apply_offset(edge.Vertexes[1].Point)
                    sketch.addGeometry(Part.LineSegment(start, end))
                    edge_count += 1
                elif isinstance(edge.Curve, Part.Circle):
                    center = apply_offset(edge.Curve.Center)
                    sketch.addGeometry(Part.Circle(center, edge.Curve.Axis, edge.Curve.Radius))
                    edge_count += 1
                elif isinstance(edge.Curve, Part.BSplineCurve):
                    # Approximate the BSplineCurve with a series of line segments
                    points = edge.discretize(Number=20)  # You can adjust the number of points
                    offset_points = [apply_offset(p) for p in points]
                    for j in range(len(offset_points) - 1):
                        sketch.addGeometry(Part.LineSegment(offset_points[j], offset_points[j+1]))
                        edge_count += 1
                    #log_print(f"  Approximated BSplineCurve with {len(points)-1} line segments")
                else:
                    log_print(f"  Unsupported curve type: {type(edge.Curve).__name__}", error=True)

            
            #log_print(f"  Added {edge_count} edges to sketch")
            
            #log_print(f"  Removing original imported object: {obj.Name}")
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

finally:
    log_print("Script ended")
    log_file.close()
    sys.exit(0)
