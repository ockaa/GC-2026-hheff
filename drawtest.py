from drawing import Draw_All_Triangulation
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
INSTANCE_FILENAME = "rirs-1000-50-efb3c1bd.json" 

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
    traings_list = []
    for triang in instance.triangulations:
        traings_list.append(FlippableTriangulation.from_points_edges(points_list, triang))
    Draw_All_Triangulation(traings_list,points_list)
if __name__ == "__main__":
    main()