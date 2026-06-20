bl_info = {
    "name": "Hotwire Slicer",
    "author": "Elias Annila",
    "version": (1, 0),
    "blender": (3, 2, 2),
    "location": "3D View > Sidebar > Slicer",
    "description": "Simulates hot wire cutting through a mesh",
    "category": "Object",
}

from . import gcode_viewer, cut_points, cut_wire, move_toolhead, insert_gcode, export_gcode
from .import ui_panel
from .import utils, axis_object


import importlib

def register():
    
    for m in [utils, axis_object]:
        importlib.reload(m)
    
    for m in [ui_panel,gcode_viewer,cut_points,cut_wire,move_toolhead,insert_gcode,export_gcode]:
        importlib.reload(m)
        m.register()
    
def unregister():
    for m in [ui_panel,gcode_viewer,cut_points,cut_wire,move_toolhead,insert_gcode,export_gcode]:
        m.unregister()
    