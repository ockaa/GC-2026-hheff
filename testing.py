from math import dist
import os
from pathlib import Path
import matplotlib.pyplot as plt

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from drawing import Draw_distance
from distance import distance
import helpFuncs
from Components import ConnectedDirectedComponent, DynamicGraphManager, MakeComponents , make_component_flip_stages,check_if_flips_is_b
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "woc-205-tsplib-8058c7cb.json" 

def main():
    # 1. Locate and Load the Instance
    print("--- 1. Loading Instance ---")
    
    script_dir = Path(__file__).parent
    instance_path = script_dir / INSTANCE_FOLDER / INSTANCE_FILENAME
    
    if not instance_path.exists():
        print(f"Error: Instance file not found at {instance_path}")
        return

    try:
        instance: CGSHOP2026Instance = read_instance(str(instance_path))
        num_triangulations = len(instance.triangulations)
        print(f"Loaded instance '{instance.instance_uid}' with {len(instance.points_x)} points and {num_triangulations} triangulations.")
        
    except Exception as e:
        print(f"Error reading instance file: {e}")
        return

    points_list = [
        Point(x, y) 
        for x, y in zip(instance.points_x, instance.points_y)
    ]
    triang1 = instance.triangulations[0]
    triang2 = instance.triangulations[1]
    a: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang1)
    b: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang2)
    


    a_clone = a.fork()
    points_coords = [(p.x(), p.y()) for p in a._flip_map.points]
    
    
    """draw_triangulation(
        points_coords, 
        a_clone.get_edges()
    )"""
    dist,stages_of_flips,l2 = distance(a.fork(),b.fork())
    print(f"Distance between triangulations before comp: {dist}")
    stages_of_flips_comp,dist_comp = make_component_flip_stages(a,stages_of_flips)
    print(f"Distance between triangulations after comp: {dist_comp}")
    print(f"do the flips lead to b {check_if_flips_is_b(a,b,stages_of_flips_comp)}")
    Draw_distance(dist_comp, stages_of_flips_comp, a,b,points_list)
if __name__ == "__main__":
    main()