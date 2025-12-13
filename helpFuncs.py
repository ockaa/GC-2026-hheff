
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


def reconstruct_triangulation_sequence(a: FlippableTriangulation, flips_by_layer):
    """
    a: FlippableTriangulation – starting triangulation
    flips_by_layer: list of sets of edges to flip at each layer
    returns: list of triangulations from A to B(B as dest trian) following the layers
    """

    current = a.fork()
    sequence = [current.fork()]   #put a in the start

    for layer_flips in flips_by_layer:
        for e in layer_flips: #do all flips that layer
            try:
                current.add_flip(e)
            except ValueError:
                continue
        current.commit() #commit the flips
        sequence.append(current.fork()) #add it

    return sequence


def independent_set(a: FlippableTriangulation, edges):
    try:
        a_tmp = a.fork()
        for e in edges:
            a_tmp.add_flip(e)
        a_tmp.commit()
        return True
    except ValueError:
        return False

def maximal_independent_subsets(a: FlippableTriangulation, candidates):
    """
    מחזירה רשימה של תתי-קבוצות בלתי תלויות מקסימליות
    """
    subsets = []

    for start in candidates:
        current = {start}
        a_tmp = a.fork()
        try:
            a_tmp.add_flip(start)
            a_tmp.commit()
        except ValueError:
            continue

        for e in candidates:
            if e in current:
                continue
            try:
                a_try = a_tmp.fork()
                a_try.add_flip(e)
                a_try.commit()
                current.add(e)
                a_tmp = a_try
            except ValueError:
                continue

        subsets.append(current)

    return subsets
