import os
from pathlib import Path
import matplotlib.pyplot as plt

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from drawing2 import Draw_distance
from distance import distance
from Fdist import distance_eppstein
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_16_15_2.json" 

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
    print("\n--- 2. Calculating Distance and Flip Sequence ---")
    dist = distance_eppstein(a.fork(),b.fork(),points_list)
    print(f"Hausdorff distance is: {dist}")
    
if __name__ == "__main__":
    main()