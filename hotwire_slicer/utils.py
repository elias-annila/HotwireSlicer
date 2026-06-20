
from mathutils import Vector
from math import fabs, radians, atan2, acos,degrees
import bpy
import bmesh
from .axis_object import AxisMapping


def insert_line(filename, text, line_number):
    # Read all lines
    with open(filename, "r") as f:
        lines = f.readlines()

    # Clamp line_number between 0 and len(lines)
    line_number = max(0, min(line_number, len(lines)))

    # Insert the text with a newline
    lines.insert(line_number, text + "\n")

    # Write back to file
    with open(filename, "w") as f:
        f.writelines(lines)
        
def insert_gcode(filename, gcode, line_number):
        # Read all lines
    with open(filename, "r") as f:
        lines = f.readlines()

    # Clamp line_number between 0 and len(lines)
    line_number = max(0, min(line_number, len(lines)))

    # Insert the text with a newline
    to_insert = [l+"\n" for l in gcode]
    lines[line_number:line_number] = to_insert

    # Write back to file
    with open(filename, "w") as f:
        f.writelines(lines)




    
def transformations_to_gcode(transformations):
    def make_line(line):
        s="G1"
        s+=''.join([f"\t\t{k}{round(v,3)}" for k,v in line.items()])
        return s
    return [make_line(l) for l in transformations]
            
def save_gcode(filename,gcode):
    with open(filename, "w") as f:
        for line in gcode:
            
            s="G1"
            s+=''.join([f"\t{k}{v:<9.3f}" for k,v in line.items()])
            
            f.write(s+"\n")


def add_keyframe(obj,frame_interval=10):
    
    
            
    #AxisMapping.check_machine_limits(obj)

    
    current_frame = bpy.context.scene.frame_current
    
    # Insert keyframe for location
    obj.keyframe_insert(data_path="location", frame=current_frame)

    # Insert keyframe for rotation (assuming rotation mode is 'XYZ' euler)
    obj.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    obj.keyframe_insert(data_path='["feedrate"]', frame=current_frame)
    current_frame +=frame_interval
    bpy.context.scene.frame_set(current_frame)




def refresh_mesh(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    # Ensure all data is available
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm

def translate(obj, axis, distance, local=False):
    """
    Translate an object along a given axis by a given distance.

    obj     : bpy.types.Object
    axis    : 'x', 'y', or 'z' (case-insensitive)
    distance: float, distance to move
    local   : bool, if True => move along local axis, else global
    """
    axis = axis.lower()
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be 'x', 'y', or 'z'")
    
    vec = Vector((0, 0, 0))
    setattr(vec, axis, distance)
    
    if local:
        # Transform vector by object's local rotation
        vec = obj.matrix_world.to_3x3() @ vec
    
    obj.location += vec
    bpy.context.view_layer.update()

def rotate(obj, axis, angle_degrees, local=False):
    """
    Rotate an object around a given axis by a given angle (in degrees)

    obj           : bpy.types.Object
    axis          : 'x', 'y', or 'z' (case-insensitive)
    angle_degrees : float, rotation amount in degrees
    local         : bool, if True => rotate around local axis, else global
    """
    axis = axis.lower()
    if axis not in ('x', 'z'):
        raise ValueError("Axis must be 'x', or 'z'")
    
    angle_radians = radians(angle_degrees)
    
    axis_i = "xyz".index(axis)
    obj.rotation_euler[axis_i]+=angle_radians
    bpy.context.view_layer.update()
    
def clear_object_keyframes(obj):
    """
    Clears all keyframes from the given object.
    
    Parameters:
    - obj: The Blender object (e.g., Empty, Mesh, Armature)
    """
    if obj.animation_data:
        obj.animation_data_clear()
        print(f"Keyframes cleared for object: {obj.name}")
    else:
        print(f"No animation data to clear for: {obj.name}")
    