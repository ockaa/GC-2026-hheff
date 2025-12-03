import os
from pathlib import Path
import matplotlib.pyplot as plt
from drawing2 import Draw_distance
from distance2 import distance
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from c_builder2 import build_flip_components
from c_builder2 import visualize_flip_components
from c_builder2 import visualize_components , optimize_flip_sequence
#from c_builder2 import full_build_components
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_4_40_2.json" 

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

    # Create the list of Point objects (the essential fix)
    points_list = [
        Point(x, y) 
        for x, y in zip(instance.points_x, instance.points_y)
    ]
    
    # 2. Setup Plotting for All Triangulations
    print("\n--- 2. Setting up Plotting ---")

    n = len(instance.triangulations)
    dist = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n): 
            # המר רשימות ל-FlippableTriangulation
            a = FlippableTriangulation.from_points_edges(points_list, instance.triangulations[i])
            b = FlippableTriangulation.from_points_edges(points_list, instance.triangulations[j])
            


            dist, stages_of_flips , stages_of_flips_with_partner = distance(a, b)
            dsu, comp_info, Trings = build_flip_components(stages_of_flips_with_partner, a)
            dist, stages_of_flips , stages_of_flips_with_partner = optimize_flip_sequence(comp_info,stages_of_flips)
            
            #visualize_flip_components(comp_info)
            visualize_components(dsu, comp_info, Trings, stages_of_flips_with_partner)
            
            Draw_distance(dist, stages_of_flips, a, b,points_list)
            #components_dict, comp_deps, deps, flip_to_comp = build_flip_components(stages_of_flips_with_partner,a)

            #visualize_all_flips_graph(components_dict, deps, flip_to_comp)
            # במקום:

            # השתמש ב:


if __name__ == "__main__":
    main()