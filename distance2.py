import os
from pathlib import Path
import matplotlib.pyplot as plt
import random

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance

def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    
    dist =0
    flips_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    set_b = set(listb)
    a_working = a.fork()
    setChangedEdges = set(normalize_edge(*e) for e in diff(lista, listb))
    
    while not a_working.__eq__(b):
        giga = 0
        setFlips = set()
        toRemove = set()
        toAdd = set()
        amount = 0
        for e in set(setChangedEdges):
            try:
                if isFree(a_working, set_b, e):
                    a_working.add_flip(e)
                    toRemove.add(e)
                    setFlips.add(e)
            except ValueError:
                continue
        
        edges_from_heuristic = Huristic(a_working, b, setChangedEdges, set_b, giga)
        
        for e in edges_from_heuristic:
            # We treat the output of the heuristic as a command to flip
            try: 
                # Safety check: ensure the heuristic didn't return an unflippable edge
                # or an edge we already flipped in the Greedy step
                if e in a_working.possible_flips() and e not in setFlips:
                    a_working.add_flip(e)
                    toRemove.add(e)
                    toAdd.add(normalize_edge(*a_working.get_flip_partner(e)))
                    setFlips.add(e)
                    amount += 1
            except ValueError:
                continue
            

        setChangedEdges -= toRemove
        setChangedEdges |= toAdd
        a_working.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        dist+=1

        print(f"{amount}")
        print(setChangedEdges)
        giga+=1


    return dist , flips_by_layer


def Huristic(
    a: FlippableTriangulation,
    b: FlippableTriangulation,
    candidates: set[tuple[int, int]],
    target_set: set[tuple[int, int]],
    giga: int
) -> set[tuple[int, int]]:
    
    edges_to_flip = deepsearch(a, target_set, depth=5, sample_size=40)
    
    return edges_to_flip



def diff(a: list[tuple[int, int]] , b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    set_a = set(a)
    set_b = set(b)
    symmetric_diff = set_a.symmetric_difference(set_b)
    return list(symmetric_diff)

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


def blocking_edges(a: FlippableTriangulation, set_b: set[tuple[int, int]],edge:tuple[int,int])-> int:
    a_temp = a.fork()
    try:
        a_temp.add_flip(edge)
        a_temp.commit()
    except ValueError:
        return 0

    # בודקים את כל האלכסונים אחרי ה-flip
    blocked = 0
    for e in a_temp.get_edges():
        flipped = normalize_edge(*a_temp.get_flip_partner(e))
        if flipped in set_b:
            blocked += 1
   
    return blocked


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
