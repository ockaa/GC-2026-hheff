import os
from pathlib import Path
import matplotlib.pyplot as plt
import random

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    k = 8
    dist =0
    flips_by_layer = list()
    flips_with_partner_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    set_b = set(listb)
    a_working = a.fork()
    setChangedEdges = set(normalize_edge(*e) for e in diff(lista, listb))
    
    while not a_working.__eq__(b):
        giga = 0
        setFlips = set()
        setFlipsWithPartner = set()
        toRemove = set()
        toAdd = set()
        amount = 0
        for e in set(setChangedEdges):
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e,flip_rev))
            except ValueError:
                continue
        edge_by_score = []
        for e in set(setChangedEdges):
            try: 
                score = blocking_edges(a_working, set_b, {e}, k)
                edge_by_score.append((e, score))
                if(score > 0):
                   print(score)

            except ValueError:
                continue
        best_edge, best_score = max(edge_by_score, key=lambda x: x[1])
        for e, score in edge_by_score:
            try: 
                if e in a_working.possible_flips():
                    if (score > 0)and e not in set_b:
                        flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                        a_working.add_flip((e))
                        toRemove.add(e)
                        toAdd.add(flip_rev)
                        setFlips.add(e)
                        setFlipsWithPartner.add((e,flip_rev))
                        amount+=1
            except ValueError:
                continue
        setChangedEdges -= toRemove
        setChangedEdges |= toAdd
        a_working.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist+=1

        print(f"{amount}")
        print(setChangedEdges)
        giga+=1


    return dist , flips_by_layer , flips_with_partner_by_layer


def Huristic(
    a: FlippableTriangulation,
    b: FlippableTriangulation,
    e: tuple[int, int],
    giga:int
) -> bool:
    
    if random.random()+0.001*giga > 0.5:
        return True
    else:
        return False
    

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
def blocking_edges(a: FlippableTriangulation, 
                   set_b: set[tuple[int, int]],
                   edges: set[tuple[int,int]], 
                   k: int) -> int:
    """
    מחשב כמה edges חופשיים ניתן להגיע אליהם מ-edges נתון
    """
    if k == 0 or not edges:
        return 0
    
    a_temp = a.fork()
    
    edge_to_partner = {}
    successful_flips = []
    
    for edge in edges:
        try:
            partner = a_temp.get_flip_partner(edge)
            edge_to_partner[edge] = partner
            a_temp.add_flip(edge)
            successful_flips.append(edge)
        except ValueError:
            continue
    
    if not successful_flips:
        return 0
    
    a_temp.commit()
    
    free_edges = set()
    blocked_edges = set()
    visited = set(edges) | set_b  
    triangles = []
    for edge in successful_flips:
        partner = edge_to_partner[edge]
        t1, t2 = new_triangles(a_temp, partner)
        triangles.append(t1)
        triangles.append(t2)
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
                else:
                    blocked_edges.add(e_norm)
    
    score = len(free_edges)
    for edge in triangles:
        if e not in free_edges and e  not in set_b and e in a_temp.possible_flips():
            try:
                a_dup = a_temp.fork()
                a_dup.add_flip(e)
                a_dup.commit()
                t1, t2 = new_triangles(a,e)
                for triangle in [t1, t2]:
                    for e in triangle: 
                       e_norm = normalize_edge(*e)
                       if isFree(a_dup, set_b, e_norm):
                         free_edges.add(e_norm)
            except ValueError:
                continue

    if free_edges:
        recursive_score = blocking_edges(a_temp, set_b, free_edges, k - 1)
        score += recursive_score

    
    return score