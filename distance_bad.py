import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from helpFuncs import normalize_edge, new_triangles, diff, isFree, maximal_independent_subsets

edge_attempt_count = defaultdict(int)

def ultra_simple_distance(a: FlippableTriangulation,
                         b: FlippableTriangulation,
                         max_iterations=25000,
                         verbose=False):
    edge_attempt_count.clear()

    k = 1
    dist = 0
    flips_by_layer = list()
    flips_with_partner_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    lastFlips = set()

    set_b = set(listb)
    a_working = a.fork()
    
    # Initial diagnostics
    initial_diff_edges = set(normalize_edge(*e) for e in diff(lista, listb))
    if verbose:
        print(f"Initial difference: {len(initial_diff_edges)} edges")
        print(f"Total edges in A: {len(lista)}, in B: {len(listb)}")
    
    setChangedEdges = initial_diff_edges
    check_cooldown = {}
    no_progress_count = 0
    
    while not a_working.__eq__(b) and dist < max_iterations:
        setFlips = set()
        setFlipsWithPartner = set()
        
        # Reset cooldown if stuck
        if no_progress_count > 10:
            if verbose:
                print(f"Iteration {dist}: Stuck detected, resetting cooldown")
            check_cooldown.clear()
            no_progress_count = 0
        
        # Filter recently checked edges
        edges_to_check = {
            e for e in setChangedEdges 
            if e not in check_cooldown or (dist - check_cooldown[e]) >= 5
        }
        
        # Phase 1: Free flips (fast!)
        free_count = 0
        for e in edges_to_check:
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                    free_count += 1
                else:
                    check_cooldown[e] = dist
            except ValueError:
                check_cooldown[e] = dist
                continue
        
        # Phase 2: Heuristic if needed
        if free_count < 3 and len(setChangedEdges) > 0:
            # Increase sample size if stuck
            sample_size = min(50 if no_progress_count > 5 else 20, len(setChangedEdges))
            sampled = set(random.sample(list(setChangedEdges), sample_size))
            
            setFlips_h, toRemove_h, toAdd_h, flips_h = Huristic_Fast(
                a_working, set_b, sampled, lastFlips, k, verbose=verbose and dist % 50 == 0
            )
            setFlips |= setFlips_h
            setFlipsWithPartner |= flips_h
        
        # Phase 3: Force a flip if completely stuck
        if len(setFlips) == 0 and len(setChangedEdges) > 0:
            if verbose:
                print(f"Iteration {dist}: Forcing random flip")
            candidates = [e for e in setChangedEdges if e in a_working.possible_flips()]
            if candidates:
                e = random.choice(candidates)
                try:
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                except:
                    pass
        
        lastFlips = setFlips.copy()
        a_working.commit()
        
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist += 1
        
        setChangedEdges = {
            normalize_edge(*e)
            for e in a_working.get_edges()
            if normalize_edge(*e) not in set_b
        }
        
        # Track progress
        if len(setFlips) == 0:
            no_progress_count += 1
        else:
            no_progress_count = 0
        
        # Debug output
        if verbose and dist % 50 == 0:
            print(f"Iteration {dist}: {len(setChangedEdges)} edges remaining, {len(setFlips)} flipped")
        
        # Permanent stuck detection
        if no_progress_count > 30:
            print(f"PERMANENTLY STUCK at iteration {dist}, {len(setChangedEdges)} edges remaining")
            return -1, flips_by_layer, flips_with_partner_by_layer
    
    if dist >= max_iterations:
        print(f"TIMEOUT: Reached {max_iterations} iterations with {len(setChangedEdges)} edges remaining")
        return -1, flips_by_layer, flips_with_partner_by_layer
    
    if verbose:
        print(f"Successfully converged in {dist} iterations")
    
    return dist, flips_by_layer, flips_with_partner_by_layer


def Huristic_Fast(
    a: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    setChangedEdges: set[tuple[int, int]],
    lastFlips: set[tuple[int, int]],
    k: int,
    verbose: bool = False
) -> tuple[set, set, set, set]:
    
    to_Flip = set()
    toRemove = set()
    toAdd = set()
    setFlipsWithPartner = set()
    
    # Pre-filter
    flippable = [
        e for e in setChangedEdges 
        if e in a.possible_flips() and e not in lastFlips and e not in set_b
    ]
    
    if not flippable:
        return set(), set(), set(), set()
    
    # Score only top candidates
    MAX_SCORE = 15
    to_score = flippable[:min(MAX_SCORE, len(flippable))]
    
    edge_by_score = []
    for e in to_score:
        try:
            score = blocking_edges_fast(a, set_b, {e}, k)
            edge_by_score.append((e, score))
        except ValueError:
            continue
    
    if not edge_by_score:
        # Random fallback
        e = random.choice(flippable)
        try:
            flip_rev = normalize_edge(*a.get_flip_partner(e))
            a.add_flip(e)
            to_Flip.add(e)
            setFlipsWithPartner.add((e, flip_rev))
            edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
        except:
            pass
        return to_Flip, set(), set(), setFlipsWithPartner
    
    # Flip best scoring edges
    best_score = max(edge_by_score, key=lambda x: x[1])[1]
    
    if verbose:
        print(f"  Heuristic: Best score = {best_score}")
    
    for e, score in edge_by_score:
        # Accept edges with score > 0 and at least 70% of best
        if score > 0 and score >= best_score * 0.7:
            try:
                flip_rev = normalize_edge(*a.get_flip_partner(e))
                a.add_flip(e)
                to_Flip.add(e)
                toRemove.add(e)
                toAdd.add(flip_rev)
                setFlipsWithPartner.add((e, flip_rev))
                edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
            except ValueError:
                continue
    
    # Final fallback
    if not to_Flip:
        candidates = [e for e in flippable if edge_attempt_count[e] == 0]
        if not candidates:
            candidates = flippable  # Any candidate is better than nothing
        
        if candidates:
            e = random.choice(candidates)
            try:
                flip_rev = normalize_edge(*a.get_flip_partner(e))
                a.add_flip(e)
                to_Flip.add(e)
                setFlipsWithPartner.add((e, flip_rev))
                edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
            except:
                pass
    
    return to_Flip, toRemove, toAdd, setFlipsWithPartner


def blocking_edges_fast(a: FlippableTriangulation, 
                        set_b: set[tuple[int, int]],
                        edges: set[tuple[int,int]], 
                        k: int) -> int:
    """Fast version - no recursion"""
    if k == 0 or not edges:
        return 0
    
    a_temp = a.fork()
    
    edge_to_partner = {}
    successful_flips = []
    
    for edge in edges:
        try:
            partner = a_temp.get_flip_partner(edge)
            edge_to_partner[edge] = partner
            if edge in a.possible_flips():
                a_temp.add_flip(edge)
                successful_flips.append(edge)
        except ValueError:
            continue
    
    if not successful_flips:
        return 0
    
    a_temp.commit()
    
    free_edges = set()
    visited = set(edges) | set_b
    
    for edge in successful_flips:
        partner = edge_to_partner[edge]
        t1, t2 = new_triangles(a_temp, partner)
        
        for triangle in [t1, t2]:
            for e in triangle:
                e_norm = normalize_edge(*e)
                
                if e_norm in visited:
                    continue
                
                visited.add(e_norm)
                
                if e_norm not in a_temp.possible_flips():
                    continue
                
                if isFree(a_temp, set_b, e_norm):
                    free_edges.add(e_norm)
    
    return len(free_edges)