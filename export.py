import sys
import FreeCAD
import Mesh
import MeshPart

# Check if the correct number of arguments is provided
if len(sys.argv) != 5:
    print("Usage: freecad export_stl.py <input_file.FCStd> <output_file.stl>")
    sys.exit(1)

# Get input and output file paths from command line arguments
input_file = sys.argv[3]
output_file = sys.argv[4]

# Open the FreeCAD file
doc = FreeCAD.open(input_file)

# Create a unified mesh from all objects
meshes = []
for obj in doc.Objects:
    if hasattr(obj, "Shape"):
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
    sys.exit(1)

# Close the document
FreeCAD.closeDocument(doc.Name)

sys.exit(0)