import os
from pathlib import Path
import matplotlib.pyplot as plt
from drawing import Draw_distance ,Draw_triangulation,Draw_All_Triangulation ,Draw_All_Triangulation_With_Distances
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from closestTriangulation import closestTringulation
#from c_builder2 import full_build_components
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_73_160_10.json" 

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

    triangs = [
        FlippableTriangulation.from_points_edges(points_list, edges)
        for edges in instance.triangulations
    ]
    n = len(instance.triangulations)
    # עכשיו אפשר לשלוח לפונקציה
    c, cTringulation ,dist = closestTringulation(triangs)
    min_i = 0
    for i in range(n):
        if(triangs[i].__eq__(cTringulation)):
            min_i = i
    Draw_All_Triangulation_With_Distances(triangs,points_list,dist,min_i)
    print(f"Closest triangulation has total distance {c}")



if __name__ == "__main__":
    main()