

import bpy
import bmesh
from mathutils import Vector, Quaternion, Euler
from mathutils.bvhtree import BVHTree
from math import fabs, radians
from bpy.types import Operator

from bpy.utils import register_class, unregister_class


from bpy.props import StringProperty

from .utils import add_keyframe,translate,rotate,clear_object_keyframes
from .axis_object import AxisMapping

class HotwireClearGcode(Operator):
    bl_idname = "hotwire.clear_gcode"
    bl_label = "Clear Gcode"
    bl_description = "Clear selected gcode file"


    def execute(self, context):
        gcode_file_name = context.scene.gcode_file_name
        open(gcode_file_name, "w").close()
        return {"FINISHED"}
  

#Operators
class HotwireViewGcode(Operator,AxisMapping):
    bl_idname = "hotwire.view_gcode"
    bl_label = "View Gcode"
    bl_description = "Simulate gcode run"

    mode="G90"

    def execute(self, context):
        
        print("EXECUTING")
        obj = bpy.context.active_object
        gcode_file_name = context.scene.gcode_file_name

        
        clear_object_keyframes(obj)
        add_keyframe(obj)
        with open(gcode_file_name, "r") as file:
            for line in file:
                
                # Strip whitespace and line breaks
                line = line.strip()
                
                # Skip empty lines or comments (comments in G-code often start with ';')
                if not line or line.startswith(';'):
                    continue
                
                commands = line.split()
                print(commands)
                if commands[0].upper() in ["G90","G91"]:
                    self.mode = commands[0].upper()
                elif commands[0].upper()=="G1":
                    print("G1->")
                    
                    
        
                    for delta in commands[1:]:
                        axis = delta[0].upper()
                        if axis not in self.axis_mapping:
                            continue
                        value=float(delta[1:])*self.unit_multiplier[axis]
                        print(f"{axis} {value}")
                        if axis in self.cartesian_axis:
                            if self.mode=="G91":
                                translate(obj,self.axis_mapping[axis],distance=value, local=axis in self.local_axis)
                            elif self.mode=="G90":
                                setattr(obj.location, axis.lower(), value)

                        elif axis in self.rotational_axis:
                            axis_i = "XYZ".index(self.axis_mapping[axis])
                            rad=radians(value)*self.unit_multiplier[axis]
                            
                            if self.mode=="G91":
                                obj.rotation_euler[axis_i]+=rad
                            elif self.mode=="G90":
                                obj.rotation_euler[axis_i]=rad

                                
                add_keyframe(obj)    
                
        
        return {'FINISHED'}


def register():
    register_class(HotwireViewGcode)
    register_class(HotwireClearGcode)

def unregister():
    unregister_class(HotwireViewGcode)
    unregister_class(HotwireClearGcode)


