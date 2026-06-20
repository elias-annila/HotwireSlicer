

import bpy
import bmesh
from mathutils import Vector, Quaternion
from bpy.types import Operator

from bpy.utils import register_class, unregister_class
from .utils import add_keyframe,translate,rotate,clear_object_keyframes, save_gcode, insert_gcode
from .axis_object import AxisMapping
import math

from bpy.props import FloatVectorProperty, BoolProperty


#Operators
class HotwireMoveToolhead(Operator, AxisMapping):
    bl_idname = "hotwire.move_toolhead"
    bl_label = "Move toolhead"
    bl_description = "Move toolhead to position"
    
    move_position:FloatVectorProperty(
        name="Move toolhead",
        description="Move toolhead to XY Position",
        subtype='TRANSLATION',   # shows as XYZ position widget
        size=2
    ) # type: ignore
    
    rot_position:FloatVectorProperty(
        name="Rotate toolhead",
        description="Rotate toolhead to ZA Position",
        subtype='EULER',   # shows as XYZ position widget
        size=2
    ) # type: ignore
    
    relative:BoolProperty(
        name="Relative",
        default=True,
        description="Absolute/relative position",
    ) # type: ignore

    def execute(self, context):
        
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        zrot = Quaternion(Vector((1,0,0)),self.rot_position[0])
           
       
        if self.relative:
            obj.location.x+= self.move_position.x
            obj.location.y+= self.move_position.y
            gcode = ["G91"]
            
            
            obj.rotation_quaternion = zrot  @ obj.rotation_quaternion
            bpy.context.view_layer.update()

            local_z = obj.matrix_world.to_3x3() @ Vector((0, 0, 1))
            arot = Quaternion(local_z,self.rot_position[1])
            obj.rotation_quaternion = arot  @ obj.rotation_quaternion


            
    
        else:
            obj.location.x= self.move_position.x
            obj.location.y= self.move_position.y
            gcode= ["G90"]
            
            obj.rotation_quaternion = zrot 
            bpy.context.view_layer.update()

            local_z = obj.matrix_world.to_3x3() @ Vector((0, 0, 1))
            arot = Quaternion(local_z,self.rot_position[1])
            obj.rotation_quaternion = arot  @ obj.rotation_quaternion            
        
        gcode.append(f"G1 A{math.degrees(self.rot_position[1])/self.unit_multiplier['A']} Z{math.degrees(self.rot_position[0])/self.unit_multiplier['Z']} X{self.move_position.x/self.unit_multiplier['X']}  Y{self.move_position.y/self.unit_multiplier['Y']}")
        
        gcode_file_name = context.scene.gcode_file_name
        line = context.scene.gcode_cursor
        insert_gcode(gcode_file_name,gcode,line)
            
        
        
        
        return {"FINISHED"}
    
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "move_position")
        layout.prop(self, "rot_position")
        layout.prop(self, "relative")
        
    def invoke(self, context, event):
        # Opens a small dialog to edit properties before execute
        return context.window_manager.invoke_props_dialog(self)
    
def register():
    register_class(HotwireMoveToolhead)

def unregister():
    unregister_class(HotwireMoveToolhead)

