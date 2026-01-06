import json
import os
from pathlib import Path
import copy

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, Point 

from closestTriangulation import closestTriangulation
from helpFuncs import reverse_flip_stages, get_formatted_path
from Components import check_if_flips_is_b

INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "rirs-1000-50-efb3c1bd.json" 
DISTANCE_RETRIES = 1 # Reduced retries since we rely on optimization now

def main():
    script_dir = Path(__file__).parent
    instance_path = script_dir / INSTANCE_FOLDER / INSTANCE_FILENAME
    
    print(f"Loading {instance_path}...")
    instance = read_instance(str(instance_path))
    
    points_list = [Point(x, y) for x, y in zip(instance.points_x, instance.points_y)]
    triangs = [FlippableTriangulation.from_points_edges(points_list, edges) for edges in instance.triangulations]

    # 1. Calculate Optimized Center and Paths
    # Note: We now unpack exactly 3 values, matching your new function definition
    final_total_dist, final_center, optimized_stages_list = closestTriangulation(triangs, retries=DISTANCE_RETRIES)
    
    print(f"Final Optimized Total Distance: {final_total_dist}")

    # 2. Reverse, Verify, and Format
    # The optimized_stages_list goes Center -> Target. We need Target -> Center.
    print("\n--- Reversing paths and verifying (Target -> Final Center) ---")
    json_paths = []
    all_valid = True
    
    for i, path_c_to_t in enumerate(optimized_stages_list):
        target_triang = triangs[i]
        
        # A. Reversal: Convert (Center -> Target) to (Target -> Center)
        path_t_to_c = reverse_flip_stages(path_c_to_t, final_center, target_triang)
        
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

    if all_valid:
        print("All paths verified successfully!")
    else:
        print("WARNING: Some paths failed verification.")

    solution_data = {
        "content_type": "CGSHOP2026_Solution",
        "instance_uid": instance.instance_uid,
        "flips": json_paths,
        "meta": {
            "dist": final_total_dist,
        },
    }

    output_path = f"solution_{instance.instance_uid}.json"
    with open(output_path, 'w') as f:
        json.dump(solution_data, f, indent=2)
    
    print(f"Saved optimized solution to {output_path}")

if __name__ == "__main__":
    main()