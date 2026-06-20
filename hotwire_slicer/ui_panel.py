from bpy.types import Panel,Operator,Scene
from bpy.utils import register_class, unregister_class
from bpy.props import FloatProperty,FloatVectorProperty, IntProperty,StringProperty
import math
from .axis_object import AxisMapping

Scene.blank_object = StringProperty(
    name="Foam blank object",
    default="Blank",
)

Scene.tool_radius = FloatProperty(
    name="Tool radius",
    default=2*AxisMapping.unit_multiplier["default"],
    min=0.0,
    max=10.0,
    subtype='DISTANCE'
)

     
Scene.safe_y = FloatProperty(
    name="Safe Y",
    default=300*AxisMapping.unit_multiplier["default"],
    min=0.0,
    max=400,
    subtype='DISTANCE'
)

Scene.interpolate_interval = FloatProperty(
    name="Interpolation interval for pocket cutting",
    default=AxisMapping.unit_multiplier["default"]*10,
    min=0.1*AxisMapping.unit_multiplier["default"],
    max=100*AxisMapping.unit_multiplier["default"],
    subtype='DISTANCE'
)



Scene.wire_interpolate_interval = FloatProperty(
    name="Interpolation interval for wire cutting",
    default=AxisMapping.unit_multiplier["default"]*1.5,
    min=0.0001,
    max=100,
    subtype='DISTANCE'
)



Scene.angle_interpolate_interval = FloatProperty(
    name="Interpolation interval rotation angle",
    default=math.radians(1.5),
    min=0.1,
    max=100,
    subtype='ANGLE'
)



Scene.max_insets = IntProperty(
    name="Max inset iterations",
    default=10,
    min=1,
    max=100,
    
)

Scene.tool_position = FloatVectorProperty(
    name="Tool position",
    description="Tool XYZ Position",
    default= (300*AxisMapping.unit_multiplier["default"],320*AxisMapping.unit_multiplier["default"],-100*AxisMapping.unit_multiplier["default"]),
    subtype='TRANSLATION',   # shows as XYZ position widget
    size=3
)

Scene.gcode_file_name = StringProperty(
    name="Gcode file",
    description="Gcode filename",
    default="~/Desktop/test.gcode",
    subtype='FILE_PATH',   # shows as XYZ position widget
)


Scene.wire_position = FloatVectorProperty(
    name="Wire position",
    description="Tool XY Position",
    default= (600*AxisMapping.unit_multiplier["default"],0*AxisMapping.unit_multiplier["default"]),
    subtype='TRANSLATION',   # shows as XYZ position widget
    size=2
)
Scene.wire_cut_radius = FloatProperty(
    name="Wire cut radius",
    description="Wire cut radius",
    default= 4*AxisMapping.unit_multiplier["default"],
    subtype='DISTANCE',   # shows as XYZ position widget
)
Scene.wire_cut_time = FloatProperty(
    name="Wire cut time",
    description="Time (s) it takes for the wire to cut it's maximum radius",
    default= 2,
    subtype='TIME', 
)
Scene.move_feedrate = FloatProperty(
    name="Move feedrate",
    description="Feedrate to use for non cutting moves",
    default= 700, 
)
Scene.wire_cut_feedrate = FloatProperty(
    name="Wire cut feedrate",
    description="Feedrate to use for wire cut moves",
    default= 100, 
)


Scene.gcode_cursor = IntProperty(
    name="Gcode line cursor",
    default=99999,
    min=0,
    
)



###Panels
class VIEW3D_PT_Slicer_Panel(Panel):
    bl_label = "Slicer"
    bl_idname = "hotwire.view_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Slicer"

    def draw(self, context):


        layout = self.layout
        box = layout.box()
        box.label(text="Gcode file")
        box.prop(context.scene, "gcode_file_name")
        box.prop(context.scene, "blank_object")
        box.operator("hotwire.view_gcode")
        box.operator("hotwire.keyframes_to_gcode")
        box.operator("hotwire.add_keyframe")


        layout.separator()
        box = layout.box()

        box.label(text="Cut pockets")
        box.operator("hotwire.cut_points")
        box.prop(context.scene, "tool_radius")  # shows editable field
        box.prop(context.scene, "tool_position")
        box.prop(context.scene, "safe_y")
        box.prop(context.scene, "max_insets")
        box.prop(context.scene, "interpolate_interval")

        
        layout.separator()
        box = layout.box()
        box.label(text="Cut wire")
        box.operator("hotwire.cut_edge_loop")
        box.operator("hotwire.cut_single_face")
        box.operator("hotwire.fatten_mesh")
        
        box.prop(context.scene, "wire_position")
        box.prop(context.scene, "wire_cut_radius")
        box.prop(context.scene, "wire_cut_time")
        box.prop(context.scene, "wire_cut_feedrate")
        box.prop(context.scene, "wire_interpolate_interval")
        box.prop(context.scene, "angle_interpolate_interval")

        
        
        layout.separator()
        box = layout.box()
        box.label(text="Insert gcode")
        box.operator("hotwire.insert_gcode")
        box.prop(context.scene, "gcode_cursor")

        
        
        
        
        


        


def register():
    register_class(VIEW3D_PT_Slicer_Panel)

def unregister():
    unregister_class(VIEW3D_PT_Slicer_Panel)
