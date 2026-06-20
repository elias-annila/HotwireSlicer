
import bpy
from mathutils import Vector, Quaternion,Euler
from bpy.types import Operator

from bpy.utils import register_class, unregister_class
from .axis_object import AxisMapping
from .utils import save_gcode
import math

#Operators
class HotwireExportGcode(Operator, AxisMapping):
    bl_idname = "hotwire.keyframes_to_gcode"
    bl_label = "Export gcode"
    bl_description = "Save animation data as gcode file"

    def execute(self, context):
        
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        gcode_file_name = context.scene.gcode_file_name
        
        gcode=HotwireExportGcode.generate_gcode(obj)
        save_gcode(gcode_file_name, gcode)
        
        return {"FINISHED"}
           
    def add_gcode_line(obj,gcode):
        rot = obj.rotation_euler
        line = {
            "X":obj.location.x/AxisMapping.unit_multiplier["X"], 
            "Y":obj.location.y/AxisMapping.unit_multiplier["Y"], 
            "Z":math.degrees(rot.x)/AxisMapping.unit_multiplier["Z"], 
            "A":math.degrees(rot.z)/AxisMapping.unit_multiplier["A"],
            "F":obj["feedrate"]
            }           
        gcode.append(line)
        
        
    def generate_gcode(obj):
        gcode = []
        keyframes = set()

        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframes.add(int(keyframe.co.x))  # keyframe.co.x is the frame number

        # Loop through sorted keyframes
        for frame in sorted(keyframes):
            bpy.context.scene.frame_set(frame)
            HotwireExportGcode.add_gcode_line(obj,gcode)
        return gcode
    
    


def register():
    register_class(HotwireExportGcode)

def unregister():
    unregister_class(HotwireExportGcode)

