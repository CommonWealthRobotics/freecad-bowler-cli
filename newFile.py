import os
import sys
import time
import traceback

import FreeCAD


def finish(code):
    # FreeCAD drops into an interactive console after a script returns, and
    # that console reads a stdin that never ends on Windows CI; the only exit
    # that cannot hang is a hard one
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run():
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 4:
        print("Usage: freecad -c create_empty_fcstd.py <output_file.FCStd>")
        print("found: ", sys.argv)
        finish(1)

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
            finish(1)

    # Create a new document
    doc = FreeCAD.newDocument()

    # Save the document
    doc.saveAs(output_file)

    print(f"Empty FreeCAD file created: {output_file}")

    # Close the document
    FreeCAD.closeDocument(doc.Name)

    finish(0)


try:
    run()
except BaseException:
    traceback.print_exc()
    time.sleep(0.2)  # let the log drain before the hard exit
    finish(1)
