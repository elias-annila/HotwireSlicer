Blender 3D addon that acts  as a slicer for hot wire cutting robot.

The robot cuts foam with a hot wire by holding the foam piece and moving it against stationary hot wire. The robot can translate on XY axis (Core XY kinematics) and rotate the workpiece on 2 additional axis. The slicer computes the robot's toolpaths and generates gcode based on Blender 3d model.

Basic principle followed by the slicer is to cut one face of a polygon model at a time following series of faces defined by edge rings and loops. A face is cut by rotating and transating the object in such a way that the wire will run along 2 edges of a quad face. Compensation for wire cutting width is done by pre-fattening the model. The slicing program first generates the toolpaths as keyframes in Blender animation system, after which the keyframes are converted to gcode. This enables easy manual tweaking of particular moves if necessary.

Bulk of the slicing logic relating to how to position the wire relative to the workpiece lives in cut_wire.py, specificaly the following methods:

* [move_to_opposing_edge](https://github.com/elias-annila/HotwireSlicer/blob/b5ee9f33dbeaa243193e8324dbee03a1d823ac29/hotwire_slicer/cut_wire.py#L239)
* [rotate_edge_to_z_axis](https://github.com/elias-annila/HotwireSlicer/blob/b5ee9f33dbeaa243193e8324dbee03a1d823ac29/hotwire_slicer/cut_wire.py#L470)

The robot itself did end up working alrgiht and i have used it for making a fixed wing plane. The chosen method of manipulating the workpiece rather than the more traditional guiding the wire from both ends did however introduce inherent challenges with precision and conveniance of use. Due to these issues I did conclude that a more traditional design would have been preferrable even if the shapes it would have been able to cut would have been more limited.


![Screenshot from blender addon ui](SlicerScreenshot.png "Screenshot from blender addon ui")
Screenshot from Blender slicer

![Cutting example](CuttingExample.jpg "Actual robot")
Actual robot cutting foam

![Plane](Plane.jpg "Robot and a plane made with it")
Robot and a plane made using it.
