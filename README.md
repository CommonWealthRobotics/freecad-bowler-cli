# freecad-bowler-cli
CLI scripts for import and exporting models into and out of Freecad

All scripts are run headlessly with FreeCAD's console binary and take their
arguments from the end of the command line (FreeCAD prepends its own args):

```
freecadcmd -c <script.py> <args...>
```

## Scripts

### newFile.py — create an empty FCStd document
```
freecadcmd -c newFile.py <output.FCStd>
```

### importSTL.py — load an STL into an FCStd as a mesh
```
freecadcmd -c importSTL.py <output.FCStd> <input.stl> <object_name>
```
Creates (or extends) `output.FCStd` with a `Mesh::Feature` named
`<object_name>_Mesh`.

### export.py — export an FCStd to STL
```
freecadcmd -c export.py <input.FCStd> <output.stl>
```
Meshes every top-level solid in the document (children of containers such as
the `Sketch`/`Pad` features inside a `PartDesign::Body` are skipped so the
same geometry is not exported twice), merges the meshes, removes duplicate
points/facets and non-manifold facets, then writes an STL. Use the FreeCAD
GUI's mesh export settings (linear/angular deflection) if you need finer
tessellation.

### importSTEP.py — load a STEP file into an FCStd as BRep solids
```
freecadcmd -c importSTEP.py <output.FCStd> <input.step> <object_name>
```
Imports exact geometry (no tessellation) using `Import.insert`, re-homes each
solid as a `Part::Feature` named `<object_name>` (or `<object_name>_<i>` when
the file holds several solids), and removes the importer's temporary
container objects.

### exportSTEP.py — export an FCStd to STEP
```
freecadcmd -c exportSTEP.py <input.FCStd> <output.step>
```
Writes every top-level shape (children skipped, see `export.py`) to a STEP
file using `Import.export`, preserving exact BRep geometry and placements.

### importSVGToPose.py — insert an SVG sketch into an FCStd body at a pose
```
freecadcmd -c importSVGToPose.py <output.FCStd> <input.svg> "<x,y,z>" "<az,el,tilt>" <slice_name> <body_name>
```
Used by BowlerStudio to add sliced geometry to a FreeCAD model.
