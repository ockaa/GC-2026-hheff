import math
import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from Fdist import cross_product, distance_eppstein
from helpFuncs import diff
def radius_flip(
    a: FlippableTriangulation,
    b: FlippableTriangulation,
    center: Point,
    n: int
):
    """Perform flips on edges within a given radius from a center point."""

    edges_to_flip = list()
    amount = 0
    a_rad = RadiusTriangulation(a.fork(), center, n)
    b_rad = RadiusTriangulation(b.fork(), center, n)
    a_edges = {normalize_edge(*e) for e in a_rad.get_edges()}
    a_edges = diff(a_edges, {normalize_edge(*eb) for eb in b_rad.get_edges()})
    print(f"            Radius flip considering {len(a_edges)} candidate edges.")
    print(f"                amount of points {a_rad._flip_map.points.__len__()} amount of edges {a_rad.get_edges().__len__()}.")
    print(f"                    is the same: {a_rad.__eq__(b_rad)}")
    for e in a_edges:
        if e not in {normalize_edge(*eb) for eb in b_rad.get_edges()}:
            try:
                amount += 1
                
                dist_before = distance_eppstein(a_rad.fork(), b_rad.fork(), a_rad._flip_map.points)
                clone_a = a_rad.fork()
                clone_a.add_flip(e)
                clone_a.commit()
                dist_after = distance_eppstein(clone_a.fork(), b_rad.fork(), a_rad._flip_map.points)
                print(f"                Radius flip on edge {e}: distance before {dist_before}, after {dist_after}.")
                if dist_after <= dist_before:
                    edges_to_flip.append(e)
            except Exception as ex:
                print(f"                Radius flip on edge {e} failed: {ex}")
                continue
    return edges_to_flip
def deepsearch(
    a: FlippableTriangulation, 
    set_b: set[tuple[int, int]], 
    depth: int = 8,
    sample_size: int = 10
) -> set[tuple[int, int]]:
    """
    Returns the edge to flip NOW that leads to the state with the 
    LEAST difference from set_b after 'depth' moves.
    """
    
    current_edges = [normalize_edge(*e) for e in a.get_edges()]
    candidates = [e for e in current_edges if e not in set_b]
    flippable_candidates = [e for e in candidates if e in a.possible_flips()]
    
    # Optimization: Random sample if too many candidates
    if sample_size is not None and len(flippable_candidates) > sample_size:
        flippable_candidates = random.sample(flippable_candidates, sample_size)

    # CHANGE 1: Init best_score to Infinity (we want to minimize diff)
    best_score = float('inf')
    best_move_set = set()

    # If no moves possible, return empty
    if not flippable_candidates:
        return set()

    for edge in flippable_candidates:
        # --- Create Copy ---
        sim_a = a.fork()
        
        # --- Commit Variation ---
        sim_a.add_flip(edge)
        sim_a.commit()
        
        # --- Greedy Step: Immediately flip any free edges ---
        # (We keep this because it's always good to flip edges that become correct)
        free_flips = get_free_flips(sim_a, set_b)
        for fe in free_flips:
            sim_a.add_flip(fe)
        sim_a.commit()
        
        # --- Recursive Step ---
        # Get the minimum difference achievable from this new state
        final_diff = _recursive_min_diff(sim_a, set_b, depth - 1, sample_size)
        
        # --- Check Winner (Minimize Score) ---
        if final_diff < best_score:
            best_score = final_diff
            best_move_set = {edge}
            
    return best_move_set
def _recursive_min_diff(
    a: FlippableTriangulation, 
    set_b: set[tuple[int, int]], 
    depth: int,
    sample_size: int
) -> int:
    """
    Helper that returns the MINIMUM difference score found in the future branches.
    """
    # 1. Base Case: If depth is 0, return the actual difference right now
    if depth <= 0:
        return calc_diff_score(a, set_b)

    current_edges = [normalize_edge(*e) for e in a.get_edges()]
    candidates = [e for e in current_edges if e not in set_b]
    flippable_candidates = [e for e in candidates if e in a.possible_flips()]
    
    # If dead end (no more flips possible), return current score
    if not flippable_candidates:
        return calc_diff_score(a, set_b)

    # Sub-sample if needed
    # if sample_size is not None and len(flippable_candidates) > sample_size:
    #    flippable_candidates = random.sample(flippable_candidates, sample_size)
        
    # We want to find the path that results in the LOWEST diff
    min_diff_branch = float('inf')
    
    for edge in flippable_candidates:
        sim_a = a.fork()
        
        sim_a.add_flip(edge)
        sim_a.commit()
        
        # Greedy optimization inside recursion
        free_flips = get_free_flips(sim_a, set_b)
        for fe in free_flips:
            sim_a.add_flip(fe)
        sim_a.commit()
        
        # Recurse
        branch_score = _recursive_min_diff(sim_a, set_b, depth - 1, sample_size)
        
        if branch_score < min_diff_branch:
            min_diff_branch = branch_score
            
    return min_diff_branch
def calc_diff_score(a: FlippableTriangulation, set_b: set[tuple[int, int]]) -> int:
    """
    Calculates how many edges in 'a' are NOT in 'set_b'.
    Lower is better.
    """
    current_edges = {normalize_edge(*e) for e in a.get_edges()}
    # The difference: Edges we have that we don't want
    diff = len(current_edges - set_b)
    return diff


def _recursive_score(
    a: FlippableTriangulation, 
    set_b: set[tuple[int, int]], 
    depth: int,
    sample_size: int
) -> int:
    """
    Helper function that returns the MAX score possible from the current state 'a'.
    """
    current_edges = [normalize_edge(*e) for e in a.get_edges()]
    candidates = [e for e in current_edges if e not in set_b]
    flippable_candidates = [e for e in candidates if e in a.possible_flips()]
    
    if not flippable_candidates:
        return 0

    #if sample_size is not None and len(flippable_candidates) > sample_size:
    #    flippable_candidates = random.sample(flippable_candidates, sample_size)
        
    max_score_branch = 0
    
    for edge in flippable_candidates:
        sim_a = a.fork()
        
        # 1. Commit Variation
        sim_a.add_flip(edge)
        sim_a.commit()
        
        # 2. Commit Free Edges
        free_flips = get_free_flips(sim_a, set_b)
        score_this_layer = len(free_flips)
        
        for fe in free_flips:
            sim_a.add_flip(fe)
        sim_a.commit()
        
        # 3. Recurse
        score_future = 0
        if depth > 1:
            score_future = _recursive_score(sim_a, set_b, depth - 1, sample_size)
            
        total = score_this_layer + score_future
        
        if total > max_score_branch:
            max_score_branch = total
            
    return max_score_branch

def get_free_flips(a: FlippableTriangulation, set_b: set[tuple[int, int]]) -> list[tuple[int, int]]:
    """Helper to identify all edges that can immediately flip into a target edge."""
    free_ones = []
    # We check all flippable edges to see if their partner is in set_b
    for e in a.possible_flips():
        if isFree(a, set_b, e):
            free_ones.append(e)
    return free_ones
def isFree(a: FlippableTriangulation, set_b: set[tuple[int, int]],edge:tuple[int,int]) -> bool:
    try:
        flipped_edge = normalize_edge(*a.get_flip_partner(edge))
        if(flipped_edge in set_b):
            return True
    except ValueError:
        return False
    return False


def normalize_edge(u, v):
    """Return the edge in a canonical form (smallest vertex first)."""
    return (min(u, v), max(u, v))
from collections import deque

from collections import deque, defaultdict
from cgshop2026_pyutils.geometry import FlippableTriangulation, Point


def RadiusTriangulation(
    a: FlippableTriangulation,
    center: Point,
    n: int
) -> FlippableTriangulation:
    
    # --- 1. Get Points & Sort by Distance ---
    try:
        all_points = a.points
    except AttributeError:
        all_points = a._flip_map.points 

    cx, cy = center[0], center[1]
    dist_map = []
    
    for idx, p in enumerate(all_points):
        # Exact arithmetic for distance squared
        dx = p[0] - cx
        dy = p[1] - cy
        d_sq = (dx * dx) + (dy * dy)
        dist_map.append((d_sq, idx))
    
    # Deterministic sort
    dist_map.sort(key=lambda x: (x[0], x[1]))
    
    # --- 2. Select Subset ---
    # Ensure we have at least 3 points, otherwise triangulation is impossible
    if len(dist_map) < 3:
        return None 
        
    limit = min(n, len(dist_map))
    subset_indices = [item[1] for item in dist_map[:limit]]
    subset_set = set(subset_indices)

    # Create mapping: Old Index -> New Index
    old_to_new = {old: new for new, old in enumerate(subset_indices)}
    new_points = [all_points[i] for i in subset_indices]

    # --- 3. Keep Existing Edges (Constraints) ---
    current_edges = []
    for u, v in a.get_edges():
        if u in subset_set and v in subset_set:
            new_u, new_v = old_to_new[u], old_to_new[v]
            # Store normalized edges
            current_edges.append(tuple(sorted((new_u, new_v))))
            
    # --- 4. Generate Candidates (Shortest First) ---
    candidates = []
    num_new = len(new_points)
    existing_edges_set = set(current_edges)

    for i in range(num_new):
        for j in range(i + 1, num_new):
            edge = (i, j)
            if edge not in existing_edges_set:
                p1 = new_points[i]
                p2 = new_points[j]
                # Exact length squared
                dx = p1[0] - p2[0]
                dy = p1[1] - p2[1]
                dist = (dx * dx) + (dy * dy)
                candidates.append((dist, edge))
    
    # Sort candidates by length
    candidates.sort(key=lambda x: x[0])

    # --- 5. Robust Greedy Fill ---
    accepted_edges = list(current_edges)
    
    for _, (u, v) in candidates:
        p_u = new_points[u]
        p_v = new_points[v]
        is_valid = True
        
        # A. Check intersection with ACCEPTED edges
        for (eu, ev) in accepted_edges:
            # Sharing a vertex is allowed
            if u == eu or u == ev or v == eu or v == ev:
                continue
            
            p_eu = new_points[eu]
            p_ev = new_points[ev]
            
            # Strict intersection check
            if segments_intersect_exact(p_u, p_v, p_eu, p_ev):
                is_valid = False
                break
        
        if not is_valid: 
            continue

        # B. Check if edge runs OVER any vertex (Collinearity)
        # This prevents invalid edges that "crush" a point on the hull boundary
        for k in range(num_new):
            if k == u or k == v:
                continue
            
            p_k = new_points[k]
            if is_point_on_segment_exact(p_k, p_u, p_v):
                is_valid = False
                break
        
        if is_valid:
            accepted_edges.append((u, v))

    # --- 6. Build ---
    # This should now satisfy is_triangulation strict checks
    try:
        return FlippableTriangulation.from_points_edges(new_points, accepted_edges)
    except ValueError:
        # Fallback: If 15 points fail, try 10, then 5. 
        # This handles cases where N points are collinear or form a degenerate shape.
        if n > 5:
             print(f"RadiusTriangulation fallback from {n} to {n - 5}")
             return RadiusTriangulation(a, center, n - 5)
        return None


# --- EXACT ARITHMETIC HELPERS ---
# --- EXACT ARITHMETIC HELPERS (Fixed for FieldNumber) ---

def get_sign(val):
    """
    Helper to determine the sign of a FieldNumber or float.
    Returns 1 if positive, -1 if negative, 0 if zero.
    """
    # Many geometry libraries expose a .sign() method for exact types
    if hasattr(val, 'sign'):
        return val.sign()
    
    # Fallback: Cast to float for comparison if .sign() is missing.
    # This is safe for > 0 or < 0 checks.
    f_val = float(val) 
    if f_val > 0: return 1
    if f_val < 0: return -1
    return 0

def segments_intersect_exact(a, b, c, d):
    """
    Checks if segment AB intersects CD strictly.
    """
    def ccw_sign(A, B, C):
        # Value = (B.x - A.x)(C.y - A.y) - (B.y - A.y)(C.x - A.x)
        val = (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0])
        return get_sign(val)

    s1 = ccw_sign(a, b, c)
    s2 = ccw_sign(a, b, d)
    s3 = ccw_sign(c, d, a)
    s4 = ccw_sign(c, d, b)

    # Proper intersection: Signs are different (1 and -1)
    # Check if (s1 != s2) AND (s1 != 0) AND (s2 != 0) ...
    # Simplified: (s1 * s2 < 0) implies they are opposite signs.
    # But we can't multiply FieldNumbers easily if they don't support it.
    
    # Explicit logic:
    ab_crosses = (s1 == 1 and s2 == -1) or (s1 == -1 and s2 == 1)
    cd_crosses = (s3 == 1 and s4 == -1) or (s3 == -1 and s4 == 1)

    return ab_crosses and cd_crosses

def is_point_on_segment_exact(p, a, b):
    """
    Returns True if point P lies strictly on segment AB (inclusive).
    """
    # 1. Collinearity Check
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    
    # Check if cross product is effectively zero
    if get_sign(cross) != 0:
        return False

    # 2. Bounding Box Check
    # We need to compare P's coordinates with A and B.
    # Since > and < might be blocked against ints, we compare FieldNumber vs FieldNumber.
    
    px, py = p[0], p[1]
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]

    # Check X bounds
    # Logic: (px - min_x) >= 0 and (max_x - px) >= 0
    # To avoid min/max functions (which might fail), we check the explicit interval.
    
    # Is px between ax and bx?
    # (px - ax) and (px - bx) must have opposite signs (or be zero)
    sign_xa = get_sign(px - ax)
    sign_xb = get_sign(px - bx)
    
    # If signs are same (and not zero), it's outside.
    # Valid states: (1, -1), (-1, 1), (0, anything), (anything, 0)
    if sign_xa * sign_xb == 1: # Both positive or both negative -> Outside
        return False

    # Check Y bounds
    sign_ya = get_sign(py - ay)
    sign_yb = get_sign(py - by)
    
    if sign_ya * sign_yb == 1:
        return False
        
    return True