

import bpy
import bmesh
from mathutils import Vector, Quaternion
from bpy.types import Operator

from bpy.utils import register_class, unregister_class
from .utils import insert_line, add_keyframe
from .axis_object import AxisMapping
import math

from bpy.props import StringProperty

class HotwireAddKeyframe(Operator):
    bl_idname = "hotwire.add_keyframe"
    bl_label = "Keyframe blank"
    bl_description = "Keyframe location and rotation on keyframe"

    def execute(self, context):
        blank =  bpy.data.objects.get(context.scene.blank_object)
        add_keyframe(blank)
       
        return {"FINISHED"}

#Operators
class HotwireInsertGcode(Operator):
    bl_idname = "hotwire.insert_gcode"
    bl_label = "Insert gcode"
    bl_description = "Insert gcode"
    
    gcode_string:StringProperty(
        name="Gcode line",
        description="Line to be inserted",
    ) # type: ignore

    def execute(self, context):
        gcode_file_name = context.scene.gcode_file_name
        line = context.scene.gcode_cursor
        insert_line(gcode_file_name, self.gcode_string, line)
        return {"FINISHED"}
    
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "gcode_string")
        
    def invoke(self, context, event):
        # Opens a small dialog to edit properties before execute
        return context.window_manager.invoke_props_dialog(self)


    
def register():
    register_class(HotwireInsertGcode)
    register_class(HotwireAddKeyframe)

def unregister():
    unregister_class(HotwireAddKeyframe)

