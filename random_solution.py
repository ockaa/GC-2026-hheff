import json
import os
from pathlib import Path
import copy
import random

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, Point 
from try_distance import distance_super_optimized
from distance import distance
from closestTriangulation import closestTringulation , median_triangulation,dynamic_median_triangulation
from helpFuncs import reverse_flip_stages, get_formatted_path
from Components import check_if_flips_is_b
from Components import fromCompToFlips
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "woc-230-tsplib-5d6e5c1d.json" 
DISTANCE_RETRIES = 1 # Reduced retries since we rely on optimization now

def main():
    script_dir = Path(__file__).parent
    instance_path = script_dir / INSTANCE_FOLDER / INSTANCE_FILENAME
    
    print(f"Loading {instance_path}...")
    instance = read_instance(str(instance_path))
    
    points_list = [Point(x, y) for x, y in zip(instance.points_x, instance.points_y)]
    triangs = [FlippableTriangulation.from_points_edges(points_list, edges) for edges in instance.triangulations]
  
    final_center = random.choice(triangs)

    final_total_dist = -1
    repeats = 5

   
    print("\n--- Reversing paths and verifying (Target -> Final Center) ---")
    json_paths = []
    all_valid = True
    final_before = final_total_dist
    final_total_dist = 0
    #final_total_dist, final_center, optimized_stages_list,_ = closestTringulation(triangs)
    final_center = random.choice(triangs)

    for i,target_triang in enumerate(triangs):
        min_distance_result = (0, set(), set())
        print(f"now calculate for t{i} and center")
        min_d = 400
        last_min = 400
        last_valid = None
        for k in range(repeats):    
            nd1,stageflips1,l1 = distance_super_optimized(target_triang, final_center)
            path_t_to_c = stageflips1
           # nd2,stageflips2,l2 = distance_super_optimized(final_center,target_triang)
            is_valid = check_if_flips_is_b(target_triang, final_center, path_t_to_c)
            if is_valid:
                d1 , path_t_to_c = fromCompToFlips(target_triang,stageflips1)
           # d2 , path_c_to_t = fromCompToFlips(final_center,stageflips2)
            d2 = 4000
            
            if(d2 < d1):
               # path_t_to_c = reverse_flip_stages(path_c_to_t, final_center, target_triang)
                d = d2
               # l = l2
            else:
                d=d1
                l = l1
            distance_result = d,path_t_to_c,l
            print(f"  t{i} and center distance : {d}")
            if min_d > d :
                min_d = d
                min_distance_result = distance_result
                is_valid = check_if_flips_is_b(target_triang, final_center, path_t_to_c)
                if is_valid:
                    print(f"   new min is good and is : {min_d}")
                    last_valid = min_distance_result
                    last_min = min_d
                else:
                    print(f"   FAILED verification! return to last min {last_min}")
                    min_distance_result = last_valid
                    min_d = last_min
            
            
           
        if last_valid is None:
            # אין מסלול תקין → fallback מהיר (למשל empty path או raise error)
            print(f"WARNING: Target {i} לא הצליח למצוא מסלול חוקי! משתמש ב-fallback")
            all_valid = False
            break
        _,path_t_to_c,_ =  min_distance_result
        final_total_dist+=min_d
        # B. Verification: Does Target + Path -> Center?
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