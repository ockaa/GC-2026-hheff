import json
import os
from pathlib import Path
import copy

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, Point 

from closestTriangulation import closestTriangulation
from helpFuncs import reverse_flip_stages, get_formatted_path
from Components import check_if_flips_is_b

def solve_instance(instance_filename, instance_folder="small_benchmark", output_folder="solutions", retries=100):
    """
    Processes a single CGSHOP2026 instance file.
    Skips processing if the solution file already exists.
    """
    
    # Setup paths
    script_dir = Path(__file__).parent
    input_path = script_dir / instance_folder / instance_filename
    output_dir_path = script_dir / output_folder
    
    # Create output directory if it doesn't exist
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: File {input_path} not found.")
        return

    print(f"--- Checking {input_path.name} ---")

    # Load Instance (Needed to get the UID for the filename check)
    # Note: If instances are massive, we could peek the JSON for UID using json.load 
    # to avoid object creation, but read_instance is safer for consistency.
    instance = read_instance(str(input_path))
    
    # Determine Output Path
    output_filename = f"{instance.instance_uid}.solution.json"
    output_path = output_dir_path / output_filename

    # CHECK: Does solution exist?
    if output_path.exists():
        print(f"  [SKIP] Solution already exists: {output_filename}\n")
        return

    # --- Start Heavy Processing ---
    print(f"  Processing new solution for {instance.instance_uid}...")
    
    points_list = [Point(x, y) for x, y in zip(instance.points_x, instance.points_y)]
    triangs = [FlippableTriangulation.from_points_edges(points_list, edges) for edges in instance.triangulations]

    # 1. Calculate Optimized Center and Paths
    final_total_dist, final_center, optimized_stages_list = closestTriangulation(triangs, retries=retries)
    
    print(f"  Final Optimized Total Distance: {final_total_dist}")

    # 2. Reverse, Verify, and Format
    json_paths = []
    all_valid = True
    
    for i, path_c_to_t in enumerate(optimized_stages_list):
        target_triang = triangs[i]
        
        # A. Reversal
        path_t_to_c = reverse_flip_stages(path_c_to_t, final_center, target_triang)
        
        # B. Verification
        is_valid = check_if_flips_is_b(target_triang, final_center, path_t_to_c)
        
        if not is_valid:
            print(f"  Target {i}: FAILED verification!")
            all_valid = False

        # C. Format for JSON
        json_ready = get_formatted_path(path_t_to_c)
        json_paths.append(json_ready)

    if all_valid:
        print("  All paths verified successfully.")
    else:
        print("  WARNING: Some paths failed verification.")

    solution_data = {
        "content_type": "CGSHOP2026_Solution",
        "instance_uid": instance.instance_uid,
        "flips": json_paths,
        "meta": {
            "dist": final_total_dist,
            "all-distances-verified": all_valid,
            "all-distances": [len(stages) for stages in optimized_stages_list],
        },
    }

    with open(output_path, 'w') as f:
        json.dump(solution_data, f, indent=2)
    
    print(f"  Saved solution to {output_path}\n")


def main():
    # Configuration
    INSTANCE_FOLDER = "small_benchmark"
    OUTPUT_FOLDER = "solutions"
    DISTANCE_RETRIES = 1

    script_dir = Path(__file__).parent
    folder_path = script_dir / INSTANCE_FOLDER
    
    if folder_path.exists():
        # Get list of all json files
        files = [f.name for f in folder_path.glob("*.json")]
        total_files = len(files)
        print(f"Found {total_files} instances in {INSTANCE_FOLDER}. Scanning for missing solutions...")
        
        for i, filename in enumerate(files, 1):
            # Optional: Print progress counter if list is long
            # print(f"File {i}/{total_files}: {filename}")
            solve_instance(filename, INSTANCE_FOLDER, OUTPUT_FOLDER, DISTANCE_RETRIES)
    else:
        print(f"Folder {INSTANCE_FOLDER} does not exist.")

if __name__ == "__main__":
    main()