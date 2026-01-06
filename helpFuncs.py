
import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance

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

def new_triangles(a: FlippableTriangulation, e: tuple[int,int]):
    u, w = e
    v, z = a.get_flip_partner(e)
    
    t1 = [normalize_edge(u,v), normalize_edge(v,z), normalize_edge(z,u)]
    t2 = [normalize_edge(v,w), normalize_edge(w,z), normalize_edge(z,v)]
    
    return t1, t2

def reverse_flip_stages(stages_of_flips: list[list[tuple[int,int]]], a: FlippableTriangulation, b: FlippableTriangulation) -> list[list[tuple[int,int]]]:
    """
    Takes a path of flips from A -> B and returns the valid path from B -> A.
    """
    # 1. We must simulate the forward path starting from A 
    # to calculate the correct 'partners' for the return trip.
    current_triang = a.fork()
    reversed_stages = []

    for stage in stages_of_flips:
        current_stage_reverse_flips = []
        
        # A. Calculate the partners (The edges needed to go back)
        for flip in stage:
            # The edge that replaces 'flip' in the current triangulation
            # is the edge we will need to flip later to undo this step.
            partner = current_triang.get_flip_partner(flip)
            
            # Normalize edge (u, v) -> (min, max) to ensure consistency
            u, v = partner
            normalized_partner = (min(u, v), max(u, v))
            current_stage_reverse_flips.append(normalized_partner)
        
        # B. Apply the forward flips to update the geometry for the next stage
        for flip in stage:
            current_triang.add_flip(flip)
        current_triang.commit()
        
        # C. Store this stage (we will reverse the order of stages at the end)
        reversed_stages.append(current_stage_reverse_flips)

    # 2. Reverse the order of the stages
    # If the path was [Step1, Step2, Step3], the reverse is [Undo3, Undo2, Undo1]
    return reversed_stages[::-1]

import json

def get_formatted_path(stages):
    """
    Converts internal edge representations into the 
    [[u, v], [x, y]] format required by the JSON schema.
    """
    formatted_stages = []
    for round_flips in stages:
        # The schema requires a list of pairs of indices
        formatted_round = [[int(e[0]), int(e[1])] for e in round_flips]
        formatted_stages.append(formatted_round)
    return formatted_stages

def save_cgshop_solution(instance_uid, all_flips, filename, algo_name="heuristic-median", dist=None):
    """
    Constructs the final JSON object and writes it to a file.
    """
    solution_data = {
        "content_type": "CGSHOP2026_Solution",
        "instance_uid": instance_uid,
        "flips": all_flips,
        "meta": {
            "algorithm": algo_name,
            "dist": dist,
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(solution_data, f, indent=2)
    print(f"Solution successfully saved to {filename}")
    