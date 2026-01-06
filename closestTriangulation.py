from cgshop2026_pyutils.geometry import FlippableTriangulation
from distance import distance
# Import your optimizer here
from Components import make_component_flip_stages
from helpFuncs import reverse_flip_stages, get_formatted_path
from Components import optimize_best_triangulation, check_if_flips_is_b
def calculate_all_dis(triangulations: list[FlippableTriangulation], retries: int = 5) -> tuple[list[list[int]], list[list[list]]]:
    n = len(triangulations)
    dist = [[0] * n for _ in range(n)]
    
    # This will store the OPTIMIZED paths
    paths = [[[] for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n): 
            min_opt_len = float('inf')
            best_opt_stages = []
            
            print(f"Optimizing {i} -> {j} ({retries} retries)...")
            
            for _ in range(retries):
                # 1. Calculate raw heuristic distance
                # We use fork() to keep T_i safe
                _, raw_stages, _ = distance(triangulations[i].fork(), triangulations[j].fork())
                while raw_stages is None:
                    print("Retrying distance calculation due to failure...")
                    _, raw_stages, _ = distance(triangulations[i].fork(), triangulations[j].fork())
                # 2. Immediately optimize this specific attempt
                opt_stages, _ = make_component_flip_stages(triangulations[i].fork(), raw_stages)
                
                # 3. Check if this is the best *optimized* length we've seen
                opt_len = len(opt_stages)
                if opt_len < min_opt_len:
                    min_opt_len = opt_len
                    best_opt_stages = opt_stages
            
            # Store the minimized OPTIMIZED distance
            dist[i][j] = min_opt_len
            dist[j][i] = min_opt_len
            
            # Store the best OPTIMIZED path
            paths[i][j] = best_opt_stages

    return dist, paths

def calculate_min_idx(arr: list[int], n: int) -> int:
    if n == 0: return -1
    min_i = 0
    for i in range(1, n):
        if arr[i] < arr[min_i]:
            min_i = i
    return min_i

def closestTriangulation(
    triangulations: list[FlippableTriangulation],
    retries: int = 5
) -> tuple[int, FlippableTriangulation, list[list[list[tuple[int,int]]]]]:
    """
    1. Calculates All-Pairs Shortest Paths (heuristic).
    2. Picks the best existing triangulation (Median).
    3. Runs Greedy Optimization to create a NEW, better center.
    
    Returns:
        (final_total_distance, optimized_center_triangulation, list_of_paths_from_center_to_targets)
    """
    n = len(triangulations)
    
    # 1. Calculate All-Pairs Heuristic Flip Distances
    print("  Calculating all-pairs distances...")
    distance_matrix, path_matrix = calculate_all_dis(triangulations, retries=retries)
    
    # 2. Find the best "start" center among the existing triangulations
    arr = [0] * n
    for i in range(n):
        for j in range(n): 
            arr[i] += distance_matrix[i][j]
            
    min_i = calculate_min_idx(arr, n)
    initial_center = triangulations[min_i]
    initial_dist = arr[min_i]
    
    print(f"  Initial median index: {min_i} (Total Dist: {initial_dist})")

    # 3. Prepare paths for the Optimizer (Center -> Target)
    # The optimizer needs a list of 'n' paths, all starting from 'initial_center'.
    paths_from_center = []

    for i in range(n):
        if i == min_i:
            paths_from_center.append([]) # Distance to self is 0
        elif i > min_i:
            # path_matrix stores paths where index1 < index2. 
            # So [min_i][i] is the path FROM min_i TO i. Correct.
            paths_from_center.append(path_matrix[min_i][i])
        else: # i < min_i
            # path_matrix stores [i][min_i] (i -> min_i).
            # We need to reverse it to get min_i -> i.
            forward_path = path_matrix[i][min_i]
            reversed_path = reverse_flip_stages(forward_path, triangulations[i], triangulations[min_i])
            paths_from_center.append(reversed_path)

    # 4. Run the Global Optimizer
    # This creates a new 'synthetic' center that minimizes the distance further.
    print("  Running greedy optimization...")
    final_center, optimized_stages_list = optimize_best_triangulation(
        paths_from_center, 
        initial_center, 
        triangulations
    )
    
    # 5. Calculate Final Total Distance (Sum of depths of optimized paths)
    final_total_dist = 0
    for stages in optimized_stages_list:
        # stages is a list of layers. The depth is the number of layers.
        final_total_dist += len(stages)

    print(f"  Optimization result: {initial_dist} -> {final_total_dist}")

    return final_total_dist, final_center, optimized_stages_list