import sys
import FreeCAD
import Mesh

# Check if the correct number of arguments is provided
if len(sys.argv) != 5:
    print("Usage: freecad export_stl.py <input_file.FCStd> <output_file.stl>")
    sys.exit(1)

# Get input and output file paths from command line arguments
input_file = sys.argv[3]
output_file = sys.argv[4]

# Open the FreeCAD file
doc = FreeCAD.open(input_file)

# Export all objects in the document to STL
Mesh.export(doc.Objects, output_file)

print(f"STL file exported successfully: {output_file}")

# Close the document
FreeCAD.closeDocument(doc.Name)

sys.exit(0)