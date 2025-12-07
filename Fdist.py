import heapq
import itertools
import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import floyd_warshall
from distance import normalize_edge  # Assuming this import exists in your project

# ==========================================
# 1. Geometric Helpers (Corrected)
# ==========================================

def cross_product(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def segments_intersect(p1, p2, p3, p4):
    """Checks if segment (p1,p2) properly intersects (p3,p4)."""
    d1 = cross_product(p3, p4, p1)
    d2 = cross_product(p3, p4, p2)
    d3 = cross_product(p1, p2, p3)
    d4 = cross_product(p1, p2, p4)

    # Segments intersect if endpoints of one are on opposite sides of the other
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    return False

def is_point_in_triangle(pt, v1, v2, v3):
    """
    Checks if point 'pt' is strictly inside triangle v1, v2, v3 using barycentric weights
    or orientation tests.
    """
    # Orientation method: pt must be on the same side of line (v1,v2) as v3, etc.
    d1 = cross_product(v1, v2, pt)
    d2 = cross_product(v2, v3, pt)
    d3 = cross_product(v3, v1, pt)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    # If it has both positive and negative cross products, it's outside.
    # If all are 0, it's on the boundary (we treat strict interior).
    return not (has_neg and has_pos)

def is_valid_flip(p_idx_1, p_idx_2, q_idx_1, q_idx_2, points):
    """
    Checks if diagonals e=(p1,p2) and f=(q1,q2) form a valid flip context.
    [cite_start]They must intersect, and the resulting quad must be convex and empty of other points[cite: 181].
    """
    a, b = points[p_idx_1], points[p_idx_2]
    c, d = points[q_idx_1], points[q_idx_2]
    
    # 1. Must properly intersect
    if not segments_intersect(a, b, c, d):
        return False
        
    # 2. Quadrilateral Emptiness Check
    # The quad is formed by {a, c, b, d} roughly in that order if intersecting.
    # We check if any OTHER point in S is strictly inside the triangles formed.
    
    quad_indices = {p_idx_1, p_idx_2, q_idx_1, q_idx_2}
    
    # Define bounding box for optimization
    xs = [p[0] for p in [a,b,c,d]]
    ys = [p[1] for p in [a,b,c,d]]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    for i, p in enumerate(points):
        if i in quad_indices:
            continue
            
        # Bounding box skip
        if not (min_x < p[0] < max_x and min_y < p[1] < max_y):
            continue
            
        # Check if point is inside triangle ABC or triangle ABD (splitting the quad)
        # Note: Since the diagonals intersect, the quad is convex. 
        # We can split it into (a, c, d) and (b, c, d) or any triangulation of the quad.
        # Actually, simpler: Split by one diagonal, say (a,b). 
        # Check triangles (a,b,c) and (a,b,d).
        if is_point_in_triangle(p, a, b, c) or is_point_in_triangle(p, a, b, d):
            return False
            
    return True

# ==========================================
# 2. QG Builder (Preprocessing)
# ==========================================

def build_qg_distance_matrix(points):
    """
    Builds the Quadrilateral Graph and computes All-Pairs Shortest Paths.
    CONVERTS input points to standard floats to avoid FieldNumber errors.
    """
    clean_points = []
    for p in points:
        try:
            clean_points.append((float(p[0]), float(p[1])))
        except (TypeError, IndexError):
            if hasattr(p, 'x') and hasattr(p, 'y'):
                clean_points.append((float(p.x), float(p.y)))
            else:
                clean_points.append(p)
    
    points = clean_points
    n = len(points)
    
    # Identify all potential diagonals
    all_edges = []
    for i in range(n):
        for j in range(i + 1, n):
            all_edges.append((i, j))
            
    edge_to_id = {edge: idx for idx, edge in enumerate(all_edges)}
    num_edges = len(all_edges)
    
    # Build Adjacency Matrix of QG
    adj = np.zeros((num_edges, num_edges), dtype=int)
    
    for i in range(num_edges):
        for j in range(i + 1, num_edges):
            u, v = all_edges[i]
            x, y = all_edges[j]
            
            if is_valid_flip(u, v, x, y, points):
                adj[i, j] = 1
                adj[j, i] = 1
                
    # [cite_start]Compute All-Pairs Shortest Paths (QG Distances) [cite: 211]
    dist_matrix = floyd_warshall(csgraph=csr_matrix(adj), directed=False, unweighted=True)
    
    return edge_to_id, dist_matrix

# ==========================================
# 3. The A* Search (Eppstein Version)
# ==========================================

def distance_eppstein(start_triangulation, target_triangulation, points):
    """
    Computes flip distance using A* with Eppstein's Heuristic (MWPM).
    """
    
    # --- PHASE 1: PREPROCESSING ---
    edge_map, qg_dists = build_qg_distance_matrix(points)
    
    target_edges = [normalize_edge(*e) for e in target_triangulation.get_edges()]
    target_indices = [edge_map[e] for e in target_edges if e in edge_map]
    
    # Helper to calculate h_E
    def h_e(current_edges):
        curr_indices = [edge_map[normalize_edge(*e)] for e in current_edges if normalize_edge(*e) in edge_map]
        
        # If sizes don't match due to mapping errors, return infinity (invalid path)
        if len(curr_indices) != len(target_indices):
            return float('inf')

        k = len(curr_indices)
        cost_matrix = np.zeros((k, k))
        
        # Fill cost matrix with Shortest Path distances from QG
        for r, u_idx in enumerate(curr_indices):
            for c, v_idx in enumerate(target_indices):
                dist = qg_dists[u_idx, v_idx]
                cost_matrix[r, c] = dist
                
        # [cite_start]Solve Assignment Problem (Hungarian Algorithm) [cite: 216]
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # [cite_start]The heuristic is the sum of the matching costs [cite: 187]
        total_cost = cost_matrix[row_ind, col_ind].sum()
        return total_cost

    # --- PHASE 2: A* SEARCH ---
    
    start_g = 0
    start_h = h_e(start_triangulation.get_edges())
    start_f = start_g + start_h
    
    tie_breaker = 0
    pq = [(start_f, start_g, tie_breaker, start_triangulation)]
    visited = set()
    
    while pq:
        f, g, _, current = heapq.heappop(pq)
        
        state_key = tuple(sorted(normalize_edge(*e) for e in current.get_edges()))
        if state_key in visited:
            continue
        visited.add(state_key)
        
        # Goal check: Distance is 0 (or very close due to floats)
        # Note: h_e returns the matching cost. If matching cost is 0, we are at target.
        if f - g < 1e-6: 
             return g
             
        # Expand Neighbors
        for edge_to_flip in current.possible_flips():
            neighbor = current.fork()
            neighbor.add_flip(edge_to_flip)
            neighbor.commit()
            
            neighbor_key = tuple(sorted(normalize_edge(*e) for e in neighbor.get_edges()))
            if neighbor_key in visited:
                continue
                
            new_g = g + 1
            new_h = h_e(neighbor.get_edges())
            new_f = new_g + new_h
            
            tie_breaker += 1
            heapq.heappush(pq, (new_f, new_g, tie_breaker, neighbor))
            
    return -1