import json
import os
from pathlib import Path
import copy

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, Point 
from try_distance import distance_super_optimized
from closestTriagWithPoints import median_triangulation_2
from closestTriangulation import closestTringulation , median_triangulation,dynamic_median_triangulation
from helpFuncs import reverse_flip_stages, get_formatted_path
from Components import check_if_flips_is_b
from c_builder import fromCompToFlips
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_110_15_3.json" 
DISTANCE_RETRIES = 1 # Reduced retries since we rely on optimization now

def main():
    script_dir = Path(__file__).parent
    instance_path = script_dir / INSTANCE_FOLDER / INSTANCE_FILENAME
    
    print(f"Loading {instance_path}...")
    instance = read_instance(str(instance_path))
    points_x = instance.points_x() if callable(instance.points_x) else instance.points_x
    points_y = instance.points_y() if callable(instance.points_y) else instance.points_y
    print(type(points_x[0]), points_x[0])
    print(type(points_y[0]), points_y[0])
    
    # יוצרים רשימת נקודות
        # נבדוק אם instance.points_x/points_y הם callable
    points_x = instance.points_x() if callable(instance.points_x) else instance.points_x
    points_y = instance.points_y() if callable(instance.points_y) else instance.points_y
    class MyPoint:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    # הופכים כל x,y ל־float/מספר אמיתי
    points_list = []
    for x, y in zip(points_x, points_y):
        if callable(x):
            x = x()
        if callable(y):
            y = y()
        points_list.append(MyPoint(x, y))
    triangs = [FlippableTriangulation.from_points_edges(points_list, edges) for edges in instance.triangulations]
    print(type(points_list[0]), points_list[0])
    
    print(f"there is {len(triangs)} triangs")
    triangs_with_min = triangs.copy()
    # 1. Calculate Optimized Center and Paths
    # Note: We now unpack exactly 3 values, matching your new function definition

    min_tiang = median_triangulation_2(triangs_with_min,points_list)
    #triangs_with_min.append(min_tiang)
    #final_total_dist, final_center, optimized_stages_list,_ = closestTringulation(triangs_with_min, True)
    final_center = min_tiang
    final_total_dist = -1
    repeats = 20
    
    # 2. Reverse, Verify, and Format
    # The optimized_stages_list goes Center -> Target. We need Target -> Center.
    print("\n--- Reversing paths and verifying (Target -> Final Center) ---")
    json_paths = []
    all_valid = True
    final_before = final_total_dist
    final_total_dist = 0
    
    for i,target_triang in enumerate(triangs):
        min_distance_result = (0, set(), set())
        print(f"now calculate for t{i} and center out of {len(triangs)}")
        min_d = 400
        last_min = 400
        last_valid = None   

        for k in range(repeats):  
            d1 = 400
            d2 = 400  
            path_t_to_c = None
            path_c_to_t = None

            nd1,stageflips1,l1 = distance_super_optimized(target_triang, final_center,points_list)
            nd2,stageflips2,l2 = distance_super_optimized(final_center,target_triang,points_list)
            is_valid = check_if_flips_is_b(target_triang, final_center, stageflips1)
            if is_valid:
                d1 , path_t_to_c = fromCompToFlips(target_triang,stageflips1)
            is_valid = check_if_flips_is_b(final_center,target_triang, stageflips2)    
            if is_valid:
               d2 , path_c_to_t = fromCompToFlips(final_center,stageflips2)

            if(d2 < d1) and path_c_to_t is not None:
                path_t_to_c = reverse_flip_stages(path_c_to_t, final_center, target_triang)
                d = d2
                l = l2
            elif path_t_to_c is not None:
                d=d1
                l = l1
            else:
                continue
            distance_result = d,path_t_to_c,l
            is_valid = check_if_flips_is_b(target_triang, final_center, path_t_to_c)
            if min_d > d and is_valid:
                min_d = d
                min_distance_result = distance_result
                last_min = min_d
                last_valid = min_distance_result
                print(f"    new min {d}")  
            elif min_d > d:
                print(f"   last run brought new min {d} but not valid solution , discarded")  
               
        _,path_t_to_c,_ =  min_distance_result
        final_total_dist+=min_d
        # B. Verification: Does Target + Path -> Center?
        if last_valid is None:
            # אין מסלול תקין → fallback מהיר (למשל empty path או raise error)
            print(f"WARNING: Target {i} לא הצליח למצוא מסלול חוקי! משתמש ב-fallback")
            all_valid = False
            break
        
        is_valid = check_if_flips_is_b(target_triang, final_center, path_t_to_c)
        
        if is_valid:
            print(f"Target {i}: Verified")
        else:
            print(f"Target {i}: FAILED verification!")
            all_valid = False

        # C. Format for JSON
        json_ready = get_formatted_path(path_t_to_c)
        json_paths.append(json_ready)
    print(f"Final Optimized Total Distance before trying to save: {final_before}")
    print(f"Final Optimized Total Distance: {final_total_dist}")
    algo_name ="heuristic-median"
    if all_valid:
        print("All paths verified successfully!")
    else:
        print("WARNING: Some paths failed verification.")
    
    solution_data = {
        "content_type": "CGSHOP2026_Solution",
        "instance_uid": instance.instance_uid,
        "flips": json_paths,
        "meta": {
            "algorithm": algo_name,
            "dist": final_total_dist,
            "notes":True
        },
    }

    output_path = f"{instance.instance_uid}.solution.json"
    with open(output_path, 'w') as f:
        json.dump(solution_data, f, indent=2)
    
    print(f"Saved optimized solution to {output_path}")

if __name__ == "__main__":
    main()