from math import inf
import numpy as np

class AxisMapping():
    cartesian_axis = ["X","Y"]
    rotational_axis= ["Z","A"]
    local_axis="A"
    
    
    axis_mapping = {
        "X":"X",
        "Y":"Y",
        "Z":"X",
        "A":"Z",
    }
    unit_multiplier = {
        "default":0.001,
        "X":-0.001,
        "Y":0.001,
        "Z":1,
        "A":-1,
    }
    
    
    location_limits={
        "X":np.array([1200, 0])*unit_multiplier["X"],
        "Y":np.array([0,360])*unit_multiplier["Y"],
        "Z":[0,0]
    }
    rotation_limits={
        "X":np.array([-1.5, 91.5])*unit_multiplier["Z"],
        "Y":[0,0],
        "Z":[-inf,inf]
    }
    
    
    
    def check_machine_limits(obj):
        for axis in "XYZ":
            if not AxisMapping.location_limits[axis][0]<=getattr(obj.location, axis.lower())<=AxisMapping.location_limits[axis][1]:
                raise Exception(f"Off limits move attempted. { obj.location}, {obj.rotation_euler}")