

import bpy
import bmesh
from mathutils import Vector, Quaternion, Euler
from bpy.types import Operator

from bpy.utils import register_class, unregister_class
from .utils import add_keyframe,translate,rotate
from .axis_object import AxisMapping
import math

class NoFacesLeft(Exception):
    """Raised when there are no more faces to process."""
    pass


#Operators
class HotwireCutPoints(Operator, AxisMapping):
    bl_idname = "hotwire.cut_points"
    bl_label = "Cut pockets"
    bl_description = "Cut point like pattern, pockets etc."
    
    def execute(self, context):
        self.tool_radius = context.scene.tool_radius
        self.tool_position=context.scene.tool_position
        self.safe_y = context.scene.safe_y
        self.max_insets = context.scene.max_insets
        self.interpolate_interval = context.scene.interpolate_interval        
    

        self.blank_obj =  bpy.data.objects.get(context.scene.blank_object)


                
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')

        self.blank_obj.rotation_euler.x=math.radians(90)/self.unit_multiplier["Z"]
        self.blank_obj.location.y=self.safe_y
        
        bpy.context.view_layer.update()

        new_obj = self.inset_face(obj, delta=self.tool_radius ,in_place=False)
        obj.select_set(False)
        
        add_keyframe(self.blank_obj)
        

        
       #Get a point above first point to be cut at safe Y distance
        mesh = new_obj.data
        current_face=[f for f in mesh.polygons if f.select]
        current_point=mesh.vertices[current_face[0].vertices[0]].co.copy()
        global_point =  new_obj.matrix_world  @ current_point

        safe_point = self.tool_position.copy()
        safe_point.y=self.safe_y
        
        


        self.move_to_point(global_point, safe_point,new_obj)

        for i in range(self.max_insets):
            mesh = new_obj.data
            current_face=[f for f in mesh.polygons if f.select]
            if current_face:
            
                current_point=mesh.vertices[current_face[0].vertices[0]].co.copy()
                global_point =  new_obj.matrix_world  @ current_point
                self.move_to_point(global_point, self.tool_position,new_obj)

                self.add_perimeter_to_gcode(current_face[0],mesh,new_obj)            
                self.inset_face(new_obj,delta=self.tool_radius*2,in_place=True)
            else:
                break
                
        self.blank_obj.location.y=self.safe_y
        add_keyframe(self.blank_obj)
        bpy.context.view_layer.update()

        bpy.ops.object.delete()
        
        return {'FINISHED'}
    def cut_to_point(self, v2,obj):
        
            #Have to first interpolate in local coords and then convert points to global one by one after each move.
            #This is due to the object being rotated at each move
            local_tool_point = obj.matrix_world.inverted() @ self.tool_position
            points=interpolate_points_on_edge(local_tool_point,v2,self.interpolate_interval)
            
            for p in points:
                self.move_to_point(obj.matrix_world @ p,self.tool_position, obj)
        
        
    def add_perimeter_to_gcode(self,face,mesh,obj):
        
        verts = face.vertices
        num_verts = len(verts)
        for i in range(num_verts):
            v2 = mesh.vertices[verts[(i + 1) % num_verts]].co
            self.cut_to_point(v2,obj)
        return v2
    
    
    def move_to_point(self,world_v1,world_v2,obj):    
        rot_A, trans_X,trans_Y=compute_rotation_y_and_translation_xy(world_v1, world_v2, obj.location)

        print(rot_A)
        obj.rotation_euler.z -=rot_A
        obj.location.x+=trans_X
        obj.location.y+=trans_Y
        
        self.blank_obj.location=obj.location
        self.blank_obj.rotation_euler=obj.rotation_euler
        
        add_keyframe(self.blank_obj)    

        bpy.context.view_layer.update()
        
        
    def inset_face(self,obj, delta, in_place=False):
        if in_place:
            mesh = obj.data

            current_face=[f for f in mesh.polygons if f.select]

            if not current_face:
                raise NoFacesLeft("No faces left to inset")
            elif len(current_face)>1:
                raise Exception("Multpile faces in in place inset")
            # Directly inset in the original object
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.inset(thickness=delta, depth=0.0)
            bpy.ops.mesh.remove_doubles(threshold=delta/2)
            bpy.ops.object.mode_set(mode='OBJECT')
            return obj

        else:
            # --- Create a clean copy ---
            src_mesh = obj.data
            bm_src = bmesh.new()
            bm_src.from_mesh(src_mesh)
            bm_src.faces.ensure_lookup_table()

            selected_faces = [p.index for p in src_mesh.polygons if p.select]
            print(selected_faces)  # List of selected face indices
            
            if len(selected_faces) != 1:
                raise Exception(f"Currently supported for only one face {selected_faces}")
            face_index = selected_faces[0]
            # Get the face to copy
            face = bm_src.faces[face_index]

            # Create a new bmesh for the copy
            bm_copy = bmesh.new()

            # Map original verts to new verts
            vert_map = {}
            for v in face.verts:
                vert_map[v] = bm_copy.verts.new(v.co)

            # Create new face in the copy mesh
            bm_copy.faces.new(vert_map[v] for v in face.verts)

            # Write the new mesh
            new_mesh = bpy.data.meshes.new(obj.name + "_face_copy")
            bm_copy.to_mesh(new_mesh)

            bm_src.free()
            bm_copy.free()

            # Create new object from mesh
            new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
            new_obj.rotation_mode = 'ZYX'
            new_obj.rotation_euler=self.blank_obj.rotation_euler
            new_obj.location = self.blank_obj.location
            
            bpy.context.collection.objects.link(new_obj)

            # Inset the face in the new object
            bpy.context.view_layer.objects.active = new_obj
            new_obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.inset(thickness=delta, depth=0.0)
            bpy.ops.mesh.remove_doubles(threshold=delta/2)

            bpy.ops.object.mode_set(mode='OBJECT')

            return new_obj

        
def interpolate_points_on_edge(current_position,target_position, interval):
    print("Interpolation")
    print("Current", current_position )
    print("Target",target_position)
    edge_length = (target_position - current_position).length
    count = max(1, int(edge_length / interval))

    points = []

    for i in range(count):  # Include last edge_b position
        t = i / count

        # Interpolated verts positions along each edge
        points.append(current_position.lerp(target_position, t))
    
    points.append(target_position)
    print(points)
    return points


def rotate_vector_to_target_y(v, target_y):
    x, y = v
    length = math.hypot(x, y)

    if abs(target_y) > length:
        raise ValueError("Target Y is outside possible range given vector length.")

    # Angle of original vector
    alpha = math.atan2(y, x)

    # Angle needed so that y' = target_y
    beta = math.asin(target_y / length)

    # Choose theta so that rotation gets us from alpha to beta
    theta = beta - alpha


    return  theta



def compute_rotation_y_and_translation_xy(v1, v2,origin=Vector((0,0,0))):
    """
    v1: Vector, initial point (world coords)
    v2: Vector, target point (world coords)
    Returns: theta (radians), translation_x, translation_y
    """
    # Delta in Y for translation
    translation_y = v2.y - v1.y
    
    if origin.z:
        raise ValueError(f"Orizin z != 0 {origin}")
    rotated=v1.copy()
    rotated-=origin
    
   
    # Work in XZ plane for rotation and X translation
    v1_xz = Vector((rotated.x, rotated.z))

    
    # Compute rotation around global Y to align XZ projection


    #theta1 = v1_xz.angle_signed(v2_xz)
    theta = -rotate_vector_to_target_y(v1_xz, v2.z)
    
    q = Quaternion(Vector((0,1,0)),theta)
    rotated.rotate(q)
    
    # Translation along global X to reach target
    translation_x = v2.x - rotated.x - origin.x
    
    return theta, translation_x, translation_y



    


def register():
    register_class(HotwireCutPoints)

def unregister():
    unregister_class(HotwireCutPoints)


