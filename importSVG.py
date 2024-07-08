import sys
import os
import FreeCAD
import importSVG
import Part
import Sketcher
import traceback

def parse_vector(vector_str):
    return FreeCAD.Vector(*map(float, vector_str.split(',')))

def parse_quaternion(quat_str):
    return FreeCAD.Rotation(*map(float, quat_str.split(',')))

try:
    # Check if the correct number of arguments is provided
    if len(sys.argv) < 6:
        raise ValueError("Usage: freecad -c script.py <input_fcstd> <input_svg> <position> <quaternion>")

    input_fcstd = sys.argv[-4]
    input_svg = sys.argv[-3]
    position = parse_vector(sys.argv[-2])
    quaternion = parse_quaternion(sys.argv[-1])

    # Open the FreeCAD file
    doc = FreeCAD.open(input_fcstd)

    # Create a new Part object to serve as the reference frame
    ref_frame = doc.addObject('Part::Feature', 'ReferenceFrame')
    ref_frame.Placement = FreeCAD.Placement(position, quaternion)

    # Import SVG
    imported_objects = importSVG.insert(input_svg, doc.Name)

    # Create sketches for each imported object
    for i, obj in enumerate(imported_objects):
        if hasattr(obj, 'Shape'):
            sketch = doc.addObject('Sketcher::SketchObject', f'SVGSketch_{i+1}')
            sketch.Placement = ref_frame.Placement
            
            # Add geometry to the sketch
            for edge in obj.Shape.Edges:
                if isinstance(edge.Curve, Part.Line):
                    sketch.addGeometry(Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[1].Point))
                elif isinstance(edge.Curve, Part.Circle):
                    sketch.addGeometry(Part.Circle(edge.Curve.Center, edge.Curve.Axis, edge.Curve.Radius))
                # Add more geometry types as needed
            
            # Remove the original imported object
            doc.removeObject(obj.Name)

    # Recompute the document
    doc.recompute()

    # Save the modified document
    doc.saveAs(input_fcstd)

    print(f"SVG imported and saved to: {input_fcstd}")

    # Close the document
    FreeCAD.closeDocument(doc.Name)

except Exception as e:
    print(f"An error occurred: {str(e)}", file=sys.stderr)
    print("Traceback:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

finally:
    # Always exit the script
    sys.exit(0)