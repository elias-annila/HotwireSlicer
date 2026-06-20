

import bpy
import bmesh
from mathutils import Vector,  Euler
from bpy.types import Operator
from bpy.props import BoolProperty

from bpy.utils import register_class, unregister_class
from .utils import add_keyframe, refresh_mesh
from .axis_object import AxisMapping
import math
import numpy as np
epsilon = 1e-5 # tolerance for "close enough to zero"


def angle_between_vectors(v1, v2):
    """
    Returns the angle in radians between two vectors.
    """
    v1 = Vector(v1).normalized()
    v2 = Vector(v2).normalized()
    dot_product = max(min(v1.dot(v2), 1.0), -1.0)  # Clamp to avoid numerical errors
    return math.acos(dot_product)



class WireCut(AxisMapping):
        
    
     
     
    def rotate_to_line_projection(self,face,proj_plane_normal):
        normal = face.normal.copy()
        
        local_z = self.blank_obj.matrix_world.to_3x3() @ Vector((0, 0, 1))
        
        
        print("Flatte")
        angle=WireCut.rotation_to_flatten_projection(normal, local_z,proj_plane_normal)
        print(normal, local_z,proj_plane_normal,math.degrees(angle))
        
        self.blank_obj.rotation_euler.z+=angle
        


    def rotation_to_flatten_projection(face_normal, rotation_axis, proj_plane_normal):
        n = face_normal.normalized()
        k = rotation_axis.normalized()
        plane_n = proj_plane_normal.normalized()
        
        # Check if already in plane
        if abs(n.dot(plane_n)) < 1e-12:
            return 0.0
        
        k_cross_n = k.cross(n)
        denom = k_cross_n.dot(plane_n)
        if abs(denom) < 1e-12:
            raise ValueError("Rotation axis is parallel to the normal; cannot rotate into plane")
        
        angle = math.atan2(-n.dot(plane_n), denom)
        return angle
     
    def keyframe_blank(self):
        add_keyframe(self.blank_obj)
    
    def edges_cross(a1, b1, a2, b2):
        """
        Returns True if the segments (a1 → b1) and (a2 → b2) cross each other.
        All inputs must be mathutils.Vector in 3D space.
        """

    
        
        dp= (b1-a1).normalized().dot((b2-a2).normalized())
        #Vectors same direction
        if np.isclose(dp,1,rtol=epsilon,atol=epsilon):
            return False
        
        #Vectors opposite directions
        if np.isclose(dp,-1,rtol=epsilon,atol=epsilon):
            return True

        v1 = (b1 - a1).normalized()
        v2 = (b2 - a2).normalized()
        # Build a local coordinate system (plane basis)
        # Use v1 as X axis, and compute Z and Y to complete right-handed system
        plane_normal = v1.cross((a2 - a1)).normalized()  # approximate normal of the plane
        if plane_normal.length == 0:
            raise ValueError("Colinear")
            
        
        # Orthonormal basis
        local_x = v1
        local_z = plane_normal
        local_y = local_z.cross(local_x)

        def to_local_2d(p):
            # Transform 3D point to 2D in local plane coordinates
            rel = p - a1
            return Vector((rel.dot(local_x), rel.dot(local_y)))

        # Project all points to local 2D plane
        a1_2d = to_local_2d(a1)
        b1_2d = to_local_2d(b1)
        a2_2d = to_local_2d(a2)
        b2_2d = to_local_2d(b2)


        def ccw(p1, p2, p3):
            return (p3.y - p1.y) * (p2.x - p1.x) > (p2.y - p1.y) * (p3.x - p1.x)

        # Check if the segments intersect using CCW rule
        return (ccw(a1_2d, b1_2d, b2_2d) != ccw(a2_2d, b1_2d, b2_2d)) and \
            (ccw(a1_2d, a2_2d, b1_2d) != ccw(a1_2d, a2_2d, b2_2d))


    def interpolate_edges_across_quad(edge_a, edge_b, interval, obj):
        """
        edge_a, edge_b: bmesh edges (opposite edges of the quad)
        interval_mm: distance between interpolated edges
        bm: bmesh object to create new edges in

        Returns: list of bmesh edges (including edge_b at the end)
        """
        eai=edge_a.index
        ebi = edge_b.index

        bm = refresh_mesh(obj)
        v_a1, v_a2 = bm.edges[eai].verts
        v_b1, v_b2 = bm.edges[ebi].verts

        # Positions as vectors
        a1_co = v_a1.co
        a2_co = v_a2.co
        
        if WireCut.edges_cross(v_a1.co,v_a2.co,v_b1.co,v_b2.co):
            b1_co = v_b2.co
            b2_co = v_b1.co

        else:
            b1_co = v_b1.co
            b2_co = v_b2.co
            
    
        #Vectors colinear, just return edges with no interpolation as wire is already in correct spot
        
        
        # Calculate length along edges  to determine interpolation count
        edge_length = (a1_co - b1_co).length
        count = max(1, int(edge_length / interval))

        edges = []

        for i in range(count):  # Include last edge_b position
            t = i / count

            # Interpolated verts positions along each edge
            v_start_pos = a1_co.lerp(b1_co, t)
            v_end_pos = a2_co.lerp(b2_co, t)

        
            # Create edge
            edges.append((v_start_pos,v_end_pos))

        #WireCut.create_mesh_from_edges (edges)
        return edges


    def create_mesh_from_edges(edge_coords_list, name="InterpolatedEdges"):
        """
        edge_coords_list: list of tuples (Vector start, Vector end)
        Creates a new mesh object with edges between these points.
        """

        # Create a new mesh and object
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bpy.context.collection.objects.link(obj)
        
        # Collect all unique vertices to avoid duplicates
        vert_coords = []
        vert_map = {}  # Vector to index mapping
        edges_indices = []

        for start, end in edge_coords_list:
            for v in (start, end):
                key = (round(v.x, 6), round(v.y, 6), round(v.z, 6))  # rounding to avoid float precision issues
                if key not in vert_map:
                    vert_map[key] = len(vert_coords)
                    vert_coords.append(v)

            edges_indices.append((vert_map[(round(start.x,6),round(start.y,6),round(start.z,6))],
                                vert_map[(round(end.x,6),round(end.y,6),round(end.z,6))]))

        # Create mesh from verts and edges, no faces
        mesh.from_pydata(vert_coords, edges_indices, [])

        mesh.update()
        return obj

    def get_edge_normal(edge):
        face_normals = [f.normal for f in edge.link_faces]

        if not face_normals:
            # Edge is not part of a face (loose edge), so no well-defined normal
            se_normal = None
        else:
            # Edge shared by multiple faces → average normals
            se_normal = sum(face_normals, Vector()).normalized()
        return se_normal
        
    
    def move_to_starting_edge(self,obj,starting_edge):
        
        
        
        print("EDGE",starting_edge.index)
        v1, v2 = starting_edge.verts
            
        se_normal = WireCut.get_edge_normal(starting_edge)
        p1 = v1.co.copy()
        p2 = v2.co.copy()


        #Since we don't know where the foam currently meets the wire(if it does at all) use constant offset
        melt_radius, slide=HotwireFatten.compute_melting(1,1,self.wire_cut_time,self.wire_cut_radius, self.wire_cut_feedrate)
                
        p1+=se_normal*melt_radius
        p2+=se_normal*melt_radius

        self.rotate_edge_to_z_axis(p1,p2,obj)
        self.keyframe_blank()
        



    def move_to_opposing_edge(self,obj, current_edge, next_edge):
        
        bm=refresh_mesh(obj)
        
        #Check the connecting vector lengths and offset accordingly

        face = (set(current_edge.link_faces) & set(next_edge.link_faces)).pop()
        face_normal = face.normal.copy()  
        
        
        c1 =current_edge.verts[0]
        c2 =current_edge.verts[1]
        
        n1 =next_edge.verts[0]
        n2 =next_edge.verts[1]
        
        if WireCut.edges_cross(c1.co,c2.co,n1.co,n2.co):
            temp = n1
            n1=n2
            n2=temp
        
        
        side1 = (n1.co-c1.co).length
        side2 = (n2.co-c2.co).length
        
        
        if side1>side2:
            offset1,slide_factor = HotwireFatten.compute_melting(side1,side2,self.wire_cut_time,self.wire_cut_radius, self.wire_cut_feedrate)
            offset2=slide_factor*offset1
        else:
            offset2,slide_factor = HotwireFatten.compute_melting(side2,side1,self.wire_cut_time,self.wire_cut_radius, self.wire_cut_feedrate)
            offset1=slide_factor*offset2
            
            
        edges = WireCut.interpolate_edges_across_quad(edge_a=current_edge, edge_b=next_edge, interval=self.wire_interpolate_step,obj=obj)
        
    
        for start,end in edges:
            bm=refresh_mesh(obj)
         
            start+=face_normal*offset1
            end+=face_normal*offset2
            
            self.rotate_edge_to_z_axis(p1=start,p2=end,obj=obj)
       
            self.keyframe_blank()
            


    def move_over_vertex(self,obj,current_edge_i,next_edge_i):
        print("MOVE OVER VERTEX")
        bm=refresh_mesh(obj)
        current_edge = bm.edges[current_edge_i]
        next_edge=bm.edges[next_edge_i]

        v1 = (set(current_edge.verts)&set(next_edge.verts)).pop() #Common vertex
        v2 = (set(current_edge.verts)-set(next_edge.verts)).pop() #Current not in next
        v3 = (set(next_edge.verts)-set(current_edge.verts)).pop() #Next not in current
        v1_i = v1.index
        
        
        current_v=v1.co-v2.co
        next_v = v3.co-v1.co
        
        if current_v.angle(next_v)<math.radians(0.1):
            #
            #Wire is already in correct place
            return
        if current_v.angle(next_v)<math.radians(5):
            edges =[(v1.co,v3.co)]
        
        else:
            #interpolated_edges = WireCut.interpolate_angles(v1.co, v3.co, v2.co)
            bm=refresh_mesh(obj)
            
            try:
                edges = WireCut.interpolate_edges_across_quad(edge_a=current_edge, edge_b=next_edge, interval=self.wire_interpolate_step*2,obj=obj)
            except ValueError:
                return
        for start,end in edges:
            
            self.rotate_edge_to_z_axis(p1=start,p2=end,obj=obj)
            
            bm=refresh_mesh(obj=obj)
            
            
            #At each step transform so that wire stays at corner vertice            
            delta=bm.verts[v1_i].co
            delta = obj.matrix_world @ delta
            
            delta= delta.to_2d()*-1
            delta=delta.to_3d()
            delta+=self.wire_position
            
            self.blank_obj.location+=delta
            bpy.context.view_layer.update()

            
            
            self.keyframe_blank()
            



    def normalize_angle(angle):
        a=angle
        
        if abs(angle) > math.pi/2:
            angle=(math.pi-abs(angle))*-np.sign(angle)
        
        
        return angle

    def step1(self, p1,p2,obj):
        
        world_p1 = obj.matrix_world @ p1
        world_p2 = obj.matrix_world @ p2
        
        vec = (world_p1 - world_p2).normalized()
        if abs(vec.x)<epsilon:
            return
        
        local_z = obj.matrix_world.to_3x3() @ Vector((0, 0, 1))
        #print("local z", local_z)
        #Project to local XY plane
        vec_projection = (vec-vec.project(local_z))
        
        
        vec_projection = vec_projection.normalized()
        #Here we can choose any vector in global YZ plane. We chooce global Y axis, unless our local Z axis is aligned with Global Y.
        # In this case we chooce global Z axis. If Local Z is aligned with Global Y, the projection of Y axis to local XY plane is vector of length 0 which causes unpredictable behavior
        
        if 1-abs(local_z.y)<epsilon:
            global_y = Vector((0,0,1))
        else:
            global_y = Vector((0,1,0))
        y_axis_projection=(global_y-global_y.project(local_z)).normalized()
        
        
        #print("VEC PROJ", vec-vec.project(local_z))
        #print("Axis proj", global_y-global_y.project(local_z))
        #Angle between projection and Y axis projection
        angle_step1 = vec_projection.angle(y_axis_projection)
        # Determine sign using cross product and the reference axis
        cross = vec_projection.cross(y_axis_projection)
        if cross.dot(local_z) < 0:
            angle_step1 *=-1
        
        angle_step1 = WireCut.normalize_angle(angle_step1)
        self.blank_obj.rotation_euler.z +=angle_step1
        
        bpy.context.view_layer.update()
        


    def step2(self,p1,p2,obj):
        world_p1 = obj.matrix_world @ p1
        world_p2 = obj.matrix_world @ p2
        vec = (world_p1 - world_p2).normalized()
        
            
        global_z = Vector((0,0,1)).normalized()
        global_x = Vector((1,0,0))
        
        
        #Angle between vec and Z axis, Note: no projections needed, they are already in YZ plane
        angle_step2 = vec.angle(global_z)
        # Determine sign using cross product and the reference axis
        cross = vec.cross(global_z)
        if cross.dot(global_x) < 0:
            angle_step2 *=-1
        
        angle_step2 = WireCut.normalize_angle(angle_step2)

        self.blank_obj.rotation_euler.x +=angle_step2
        bpy.context.view_layer.update()

        
    def step3(self, p1,p2,obj):
        #Recompute edge endpoints in world space after rotations 
        
        world_p1 = obj.matrix_world @ p1
   
        # Compute average Y and X in world space, pointless after transformations p1 and p2 have same x and y
        
        world_p1.z=0
        delta=-world_p1
        delta+=self.wire_position
        
        self.blank_obj.location += delta
        
        bpy.context.view_layer.update()

    def check_points(p1,p2):
        if p2.z>p1.z:
            p2_temp=p2
            p2=p1
            p1=p2_temp
        return p1,p2
        
    def compute_feedrate(self,wp1_old, wp2_old, wp1,wp2, old_loc,old_rot_euler,loc,rot_euler):
        #Compute machine feedrate to move to edge keeping root speed constant.
        
        
        d1 =(wp1_old-wp1).length
        d2 =(wp2_old-wp2).length
        
        wire_distance = max(d2,d1)
        
        
        dx = old_loc.x-loc.x
        dy = old_loc.y-loc.y
        dz= old_rot_euler.x- rot_euler.x
        da =old_rot_euler.z-rot_euler.z
        
        
        um=AxisMapping.unit_multiplier["default"]
        
        machine_distance = math.sqrt((dx/um)**2+(dy/um)**2+(math.degrees(dz))**2+(math.degrees(da))**2) #Distance the machine thinks it's moving.
        
        target_speed = self.wire_cut_feedrate/60/1000

        time_to_move=wire_distance/target_speed
        
        
        if time_to_move != 0:
            machine_speed = machine_distance/time_to_move
            machine_feedrate = machine_speed*60 
            self.blank_obj["feedrate"] = machine_feedrate
        bpy.context.view_layer.update()

    def rotate_edge_to_z_axis(self,p1,p2,obj):
        
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)



     
        if obj.rotation_mode != 'ZYX' or self.blank_obj.rotation_mode!='ZYX':
            raise Exception(f"Incorrect rotation mode Blank:{self.blank_obj.rotation_mode}, Obj: {obj.rotation_mode}")
    
        
        old_loc = self.blank_obj.location.copy()
        old_rot_euler=  self.blank_obj.rotation_euler.copy()
        p1,p2 = WireCut.check_points(p1,p2)
        
        wp1_old = obj.matrix_world @ p1
        wp2_old = obj.matrix_world @ p2
        bpy.ops.object.mode_set(mode='OBJECT')
        #FIRST STEP:
        #Rotate around local Z so that edge vector has no x component
        self.step1(p1,p2,obj)
        #SECOND STEP:
        #Rotate around global X axis until edge vector has no y component
        self.step2(p1,p2,obj)
        
        #THIRD STEP:
        #Translate in XY plane so that rotated edge is located at (0,0)
        self.step3(p1,p2,obj)
        
        wp1 = obj.matrix_world @ p1
        wp2 = obj.matrix_world @ p2
        
    
        #FOURTH STEP
        #Compute machine feedrate, in taper, keep root feedrate fixed.
        self.compute_feedrate(wp1_old, wp2_old, wp1, wp2,old_loc,old_rot_euler,self.blank_obj.location,self.blank_obj.rotation_euler)

        
        
        bpy.ops.object.mode_set(mode='EDIT')
        
      


#Operators
class HotwireCutEdgeLoop(Operator, WireCut):
    bl_idname = "hotwire.cut_edge_loop"
    bl_label = "Cut edge rings following edge loop"
    bl_description = "Cut edge rings following edge loops"
    
    wire_position=Vector((0,0,0))
    
    
    
    reverse_direction:BoolProperty(
        name="Reverse first ring direction",
        default=False,
        description="",
    ) # type: ignore

    
      
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "reverse_direction")
        
    def invoke(self, context, event):
        # Opens a small dialog to edit properties before execute
        return context.window_manager.invoke_props_dialog(self)
    
    def cut_rings_following_loop(self,ring_start_edges):
        obj = bpy.context.active_object
        bm = refresh_mesh(obj)
        if not ring_start_edges:
            selected_edges = [e.index for e in bm.edges if e.select]    
            ring_start_edges = HotwireCutEdgeLoop.get_ordered_selected_edge_indices_loop(obj=obj,selected_edge_indices=selected_edges)
            
        last_edge_i = -1
        for i,edge_i in enumerate(ring_start_edges):
            ring = list(HotwireCutEdgeLoop.follow_edge_ring(start_edge_i=edge_i,obj=obj,reverse_direction=self.reverse_direction))
            
            
            print(i,last_edge_i)
            print("RING",ring)
            
        
            #Reverse every other ring. This allows following open rings along a line
            if i%2:
                print("reverse", i)
                ring.reverse()                
            
            if last_edge_i != -1: #Important, last_edge_i could be 0, which is valid index
                self.move_over_vertex(obj=obj, current_edge_i=last_edge_i,next_edge_i=ring[0])
            print("Cut edge ring")
            last_edge_i=self.cut_edge_ring(obj=obj, ring=ring)
            
    
    
    def follow_edge_ring(start_edge_i,obj, reverse_direction=False):
        
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        # Ensure all data is available
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        visited = set()
        edge = bm.edges[start_edge_i]

        def move_to_opposite_side(e):
            # Find the next edge across the face ring
            linked_faces = [f for f in e.link_faces if len(f.edges) == 4]

    
            # Find the opposite edge in the loop
            faces = linked_faces
            
            if reverse_direction:
                faces = reversed(linked_faces)

            for face in faces:
                loop = face.loops
                for l in loop:
                    if l.edge == e:
                        # The opposite edge is two steps over in a quad
                        opposite_edge = l.link_loop_next.link_loop_next.edge
                        if opposite_edge.index not in visited:
                            e = opposite_edge
                            break
                if e.index not in visited:
                    break
            return e


        #Loop following opposite edges
    
        while edge and edge.index not in visited:
            visited.add(edge.index)
            yield edge.index
            if mesh.edges[edge.index].use_seam and edge.index!=start_edge_i:
                print("Break to seam")
                break
            
            edge=move_to_opposite_side(edge)
            
        #Check if edges form a closed loop. (if next edge would have been starting edge)
        visited.remove(start_edge_i)
        if move_to_opposite_side(edge).index==start_edge_i and len(visited)>1:
            yield start_edge_i
        
            

    
    def cut_edge_ring(self,obj,ring,reversed=False):
        print("cut ring")
        
        bm=refresh_mesh(obj)
        if reversed:
            ring.reverse()
        prev_edge_i=ring[0]
        
        
        
        
        for next_edge_i in ring[1:]:
            bm=refresh_mesh(obj=obj)
            
            prev_edge=bm.edges[prev_edge_i]
            next_edge = bm.edges[next_edge_i]
            
            
            
            
            #self.move_to_starting_edge(obj=obj,starting_edge=prev_edge)
            self.move_to_opposing_edge(obj=obj, current_edge=prev_edge, next_edge=next_edge)
            prev_edge_i=next_edge_i
        
        
        
        #Cut from last interpolated edge to starting edge
        bm = refresh_mesh(obj=obj)
        self.move_to_starting_edge(obj=obj, starting_edge=bm.edges[ring[-1]])
        return ring[-1]

    
    def get_ordered_selected_edge_indices_loop(obj,selected_edge_indices):
        assert obj and obj.type == 'MESH', "Active object must be a mesh"

        if not selected_edge_indices:
            return []

        # Build vertex-to-edges map
        v_to_edges = {}
        
        bm=refresh_mesh(obj)
        selected_edges = [bm.edges[i] for i in selected_edge_indices]
        for e in selected_edges:
            for v in e.verts:
                v_to_edges.setdefault(v, []).append(e)

        # Find endpoint for open loop (a vertex connected to only one selected edge)
        endpoints = [v for v, edges in v_to_edges.items() if len(edges) == 1]
        is_open = len(endpoints) == 2

        # Start from endpoint (open loop) or any edge (closed loop)
        start_edge = selected_edges[0]
        if is_open:
            start_vert = endpoints[0]
            for e in v_to_edges[start_vert]:
                if e in selected_edges:
                    start_edge = e
                    break
        else:
            # Closed loop — start from any edge and vertex
            start_vert = start_edge.verts[0]

        ordered_edges = []
        visited_edges = set()
        current_vert = start_vert
        current_edge = start_edge

        while current_edge and current_edge not in visited_edges:
            ordered_edges.append(current_edge.index)
            visited_edges.add(current_edge)

            # Find the next edge connected to current_vert that hasn't been visited
            next_vert = [v for v in current_edge.verts if v != current_vert][0]
            next_edges = [e for e in v_to_edges[next_vert] if e != current_edge and e in selected_edges and e not in visited_edges]

            current_vert = next_vert
            current_edge = next_edges[0] if next_edges else None

        return ordered_edges


    
    def execute(self, context):

        self.wire_position = context.scene.wire_position.to_3d()
        self.angle_interpolate_step = context.scene.angle_interpolate_interval
        self.wire_interpolate_step = context.scene.wire_interpolate_interval
        self.blank_obj =  bpy.data.objects.get(context.scene.blank_object)
        self.wire_cut_radius=context.scene.wire_cut_radius
        self.wire_cut_time=context.scene.wire_cut_time
        self.wire_cut_feedrate = context.scene.wire_cut_feedrate
        

        try:
            for c in self.blank_obj.constraints:
                if c.type in  ['LIMIT_LOCATION','LIMIT_ROTATION']:
                    c.mute = True
        


            self.cut_rings_following_loop(ring_start_edges=False)
        finally:
            for c in self.blank_obj.constraints:
                if c.type in  ['LIMIT_LOCATION','LIMIT_ROTATION']:
                    c.mute = False

            
            bpy.ops.object.mode_set(mode='OBJECT')
        
        return {"FINISHED"}


    
class HotwireFatten(Operator):
    bl_idname = "hotwire.fatten_mesh"
    bl_label = "Fatten mesh"
    bl_description = "Fatten mesh to account for wire melt"
   
    
    def fatten_object(self,obj):
        
        # --- PARAMETERS ---
        extrude_amount = self.extrude_amount   # e
        slide_factor = self.slide_factor     # s (1 = no slide, 2 = Double, 0 = no extrusion)
        loop_a_name = self.root
        loop_b_name = self.tip

        mesh = obj.data

        # Make sure we are in edit mode
        bpy.ops.object.mode_set(mode='EDIT')

        bm = refresh_mesh(obj)

        # Ensure vertex groups exist
        vg_a = obj.vertex_groups.get(loop_a_name)
        vg_b = obj.vertex_groups.get(loop_b_name)
        if not vg_a or not vg_b:
            raise ValueError("Vertex groups not found")

       # Helper to get BMVerts in a vertex group
        def verts_in_group(vgroup):
            verts = []
            for v in bm.verts:
                # obj.data.vertices[v.index] gives the original vertex
                w = obj.data.vertices[v.index].groups
                if any(g.group == vgroup.index for g in w):
                    verts.append(v)
            return verts

        verts_a = verts_in_group(vg_a)
        verts_b = verts_in_group(vg_b)

        # --- STEP 1: Extrude faces along normals ---
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        extrude_result = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        extruded_geom = extrude_result['geom']

        # Move extruded vertices along normals
        extruded_verts = [v for v in extruded_geom if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(
            bm,
            verts=extruded_verts,
            vec=(0,0,0)  # placeholder
        )

        # Move each extruded vertex along its normal
        for v in extruded_verts:
            normal = v.normal
            v.co += normal * extrude_amount

        extruded_b_verts=[]
        # After extruding faces and getting extruded_verts
        for v in extruded_verts:
            # Check if original vertex belongs to B
            
            for lf in v.link_faces:
                for linked_vert in lf.verts:  # get connected original verts
                    if linked_vert in verts_b:
                        extruded_b_verts.append(v)
                        break
        # --- STEP 3: Edge slide ---
        # Find edges connected to extruded B vertices that go towards original B vertices
        edges_to_slide = []
        for v in extruded_b_verts:
            for e in v.link_edges:
                other = e.other_vert(v)
                if other in verts_b:  # connected to original
                    edges_to_slide.append((e, v,other))


        for v in verts_b:
            v.select=True

        # Slide vertices along edges
        
        for e, v_extrude, v_orig in edges_to_slide:
            direction = v_orig.co - v_extrude.co
            #e.select=True
            v_extrude.co = v_orig.co+direction.normalized()*slide_factor*extrude_amount

        # --- STEP 4: Delete extrusion edges connecting old and new vertices ---

        # Update mesh
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        
        bmesh.update_edit_mesh(mesh)

    def edge_loop_length(obj, vgroup_name):
        """
        Compute the total length of an edge loop defined by a vertex group.

        Args:
            obj: Blender mesh object in edit mode or object mode.
            vgroup_name: Name of the vertex group defining the loop.

        Returns:
            Total length of the edge loop.
        """
        # Get the vertex group
        vg = obj.vertex_groups.get(vgroup_name)
        if not vg:
            raise ValueError(f"Vertex group '{vgroup_name}' not found")

        # Access the mesh via bmesh
        if bpy.context.object.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        # Find all vertices in the group
        verts_in_group = {v.index for v in bm.verts if any(g.group == vg.index for g in obj.data.vertices[v.index].groups)}

        # Find all unique edges connecting vertices in the group
        edges_in_group = set()
        for e in bm.edges:
            if e.verts[0].index in verts_in_group and e.verts[1].index in verts_in_group:
                edges_in_group.add(e)

        # Compute total length
        total_length = sum((e.verts[0].co - e.verts[1].co).length for e in edges_in_group)

        # Free temporary bmesh if created
        if bpy.context.object.mode != 'EDIT':
            bm.free()

        return total_length
    
    def melt_curve(t, melt_radius, melt_time):
        
        return melt_radius*(1-math.e**(-t/melt_time))
        
    
    def compute_melting(length_root,length_tip, melt_time, melt_radius, feed_rate):
        
        print(feed_rate, length_tip,length_root)
        feed_rate= feed_rate/60/1000#mm/min to m/s
        
        root_speed = feed_rate
        tip_speed = feed_rate*(length_tip/length_root)
        
        time_spent_at_melt_rad_root = 0.001/root_speed 
        time_spent_at_melt_rad_tip = 0.001/tip_speed 
        
        
        root_melt = HotwireFatten.melt_curve(time_spent_at_melt_rad_root, melt_radius, melt_time)
        tip_melt = HotwireFatten.melt_curve(time_spent_at_melt_rad_tip, melt_radius, melt_time)
      
        slide_factor=tip_melt/root_melt
      
        return root_melt,slide_factor
    
    def execute(self, context):
        bpy.ops.object.duplicate()
        obj = bpy.context.active_object
        
        self.root="Root"
        self.tip="Tip"
        
          
        length_root = HotwireFatten.edge_loop_length(obj,self.root)
        length_tip = HotwireFatten.edge_loop_length(obj,self.tip)
      
        self.extrude_amount,self.slide_factor = HotwireFatten.compute_melting(length_root,length_tip,context.scene.wire_cut_time,context.scene.wire_cut_radius, context.scene.wire_cut_feedrate)
        print("SLIDE FAC", self.slide_factor)
        self.fatten_object(obj)
  
        return {"FINISHED"}
class HotwireOrientZRotation(Operator,WireCut):
    bl_idname = "hotwire.orient_a_rotation"
    bl_label = "Flatten to view"
    bl_description = "Rotate around A to flatten face in XY"
   
    def is_view_aligned(view_dir, target, tol=1e-3):
        """Check if view_dir is aligned with target vector (within tolerance)."""
        view_dir = view_dir.normalized()
        target = Vector(target).normalized()
        return abs(view_dir.dot(target) - 1.0) < tol
    def execute(self, context):
        
        raise Exception("Not implemented")
        self.blank_obj =  bpy.data.objects.get(context.scene.blank_object)
        self.wire_position = context.scene.wire_position.to_3d()
        obj = bpy.context.active_object

        bm = refresh_mesh(obj)

        selected_faces = [f for f in bm.faces if f.select]
        
        if len(selected_faces)!=1:
            raise(Exception("Select one face"))
        
        f= selected_faces[0]
       
        
        for area in bpy.context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        break

        view_dir = region_3d.view_rotation @ Vector((0.0, 0.0, 1.0))
        
        if  not(HotwireOrientZRotation.is_view_aligned(view_dir, Vector((0,0,1))) or HotwireOrientZRotation.is_view_aligned(view_dir, Vector((0,-1,0)))):
            raise Exception("View not aligned")
        
        self.rotate_to_line_projection(f,view_dir)
        
        self.keyframe_blank()
        
        return {"FINISHED"}


        
    
    
#Operators
class HotwireCutSingleFace(Operator, WireCut):
    bl_idname = "hotwire.cut_single_face"
    bl_label = "Move Wire to an edge"
    bl_description = "Move the piece so that selected edge is aligned with wire"
   
    def execute(self, context):
        
        
        try:
            self.blank_obj =  bpy.data.objects.get(context.scene.blank_object)
            
            for c in self.blank_obj.constraints:
                if c.type in  ['LIMIT_LOCATION','LIMIT_ROTATION']:
                    c.mute = True
        
            
            self.wire_position = context.scene.wire_position.to_3d()
            obj = bpy.context.active_object

            self.wire_cut_feedrate = context.scene.wire_cut_feedrate
            bm = refresh_mesh(obj)
            
            self.angle_interpolate_step = context.scene.angle_interpolate_interval
            self.wire_interpolate_step = context.scene.wire_interpolate_interval
            self.wire_cut_radius=context.scene.wire_cut_radius
            self.wire_cut_time=context.scene.wire_cut_time
            
            
            



            selected_edges = [e for e in bm.edges if e.select]
            self.move_to_starting_edge(obj,selected_edges[0])
        
        finally:
            for c in self.blank_obj.constraints:
                if c.type in  ['LIMIT_LOCATION','LIMIT_ROTATION']:
                    c.mute = False


        
        bpy.ops.object.mode_set(mode='OBJECT')

        return {"FINISHED"}
    
    
    
    


def register():
    register_class(HotwireCutEdgeLoop)
    register_class(HotwireCutSingleFace)
    register_class(HotwireOrientZRotation)
    register_class(HotwireFatten)

def unregister():
    unregister_class(HotwireCutEdgeLoop)
    unregister_class(HotwireCutSingleFace)
    unregister_class(HotwireOrientZRotation)
    unregister_class(HotwireFatten)


