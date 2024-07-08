import sys
import FreeCAD

# Check if the correct number of arguments is provided
if len(sys.argv) != 4:
    print("Usage: freecad -c create_empty_fcstd.py <output_file.FCStd>")
    print("found: ",sys.argv)
    
    sys.exit(1)

output_file = sys.argv[3]
if not os.path.exists(output_file):
    print(f"File does not exist: {output_file}")
    print("Creating a new file...")
    doc = FreeCAD.newDocument()
    doc.saveAs(output_file)
else:
    try:
        doc = FreeCAD.open(output_file)
    except Exception as e:
        print(f"Error opening file: {e}")
        sys.exit(1)

# Create a new document
doc = FreeCAD.newDocument()

# Save the document
doc.saveAs(output_file)

print(f"Empty FreeCAD file created: {output_file}")

# Close the document
FreeCAD.closeDocument(doc.Name)

sys.exit(0)

