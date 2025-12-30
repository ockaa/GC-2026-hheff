import os
from pathlib import Path
import matplotlib.pyplot as plt
from drawing import Draw_distance  ,Draw_All_Triangulation_With_Distances,Save_All_To_PDF
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from closestTriangulation import closestTringulation , median_triangulation

#from c_builder2 import full_build_components
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "woc-235-tsplib-8c89c7cb.json" 

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
# חישוב המרחקים והטריאנגולציה הקרובה
    #min_tiang = median_triangulation(triangs)
    #triangs.append(min_tiang)
    total_dist, closest_tri, dist_matrix,min_i = closestTringulation(triangs)#,True)
    print(f"closest dist id {total_dist}")
    # שמירת הכל ל-PDF
    name_without_ext = Path(INSTANCE_FILENAME).stem

# יצירת שם חדש עם סיומת PDF
    pdf_filename = f"{name_without_ext}.pdf"
    Save_All_To_PDF(triangs, points_list, dist_matrix, min_i,pdf_filename)#,True)

    #print(f"Closest triangulation has total distance {c}")



if __name__ == "__main__":
    main()