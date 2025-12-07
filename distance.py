import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from helpFuncs import normalize_edge , new_triangles,diff,isFree
from radius import radius_flip
edge_attempt_count = defaultdict(int)

def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    k = 16
    dist =0
    troubles_in_paradise = 0
    flips_by_layer = list()
    flips_with_partner_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    lastFlips = set()

    set_b = set(listb)
    a_working = a.fork()
    setChangedEdges = set(normalize_edge(*e) for e in diff(lista, listb))
    while not a_working.__eq__(b):
        setChangedEdges = set(normalize_edge(*e) for e in diff([normalize_edge(*e) for e in a_working.get_edges()], [normalize_edge(*e) for e in b.get_edges()]))
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
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                    amount+=1
            except ValueError:
                continue
        
        candients,secondFlip = Huristic( a_working, set_b,   setChangedEdges, lastFlips, k , b)
        for e in candients:
            try:
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    toAdd.add(flip_rev)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e,flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                    amount+=1
            except ValueError:
                print(f"could not flip edge {e} in first flip")
                pass
        for e in secondFlip:
            try:
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    toAdd.add(flip_rev)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e,flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                    amount+=1
            except ValueError:
                is_in_possible_flips = e in a_working.possible_flips()
                print(f"could not flip edge {e} in second flip :{is_in_possible_flips}")
                pass
        
        setChangedEdges -= toRemove
        setChangedEdges |= toAdd
        lastFlips = setFlips.copy()

        a_working.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist+=1
        if(dist > 65):
            print(f"too manny troubles in paradise")
            
            break
        #print(f"num of flips : {amount}")
        giga+=1
        print(f"Flipped {setFlips}")
        print(f"too manny troubles in paradise {dist}")
        print(f"remaining edges to fix: {len(setChangedEdges)}")

    return dist , flips_by_layer , flips_with_partner_by_layer

def Huristic(
    a: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    setChangedEdges: set[tuple[int, int]],
    lastFlips: set[tuple[int, int]],
    k: int,
    b: FlippableTriangulation
) -> list[tuple[int, int]]:
       
        edge_by_score = []
        to_Flip = set()
        secondFlip = set()
        for e in set(setChangedEdges):
            if e in a.possible_flips():
                score = blocking_edges(a, set_b, {e}, k)
                edge_by_score.append((e, score))

        best_edge, best_score = max(edge_by_score, key=lambda x: x[1])


        for e, score in edge_by_score:
            flip_rev = normalize_edge(*a.get_flip_partner(e))
            if e in a.possible_flips() and flip_rev not in lastFlips:
                if (score > 0)and e not in set_b:
                    to_Flip.add(e)


        
        if best_score == 0:
            all_points = a._flip_map.points
            candidates = [e for e in setChangedEdges if e in a.possible_flips()]
            print(f"candidates are {candidates}")
            for e in candidates:
                
                if e in a.possible_flips():
                    if secondFlip.__len__() > 5:
                        return to_Flip ,secondFlip
                    
                    vertex_index = e[0]
                
                    center_point = all_points[vertex_index]

                    edges = radius_flip(a.fork(), b.fork(), center_point, 7)
                    
                    for edge in edges:
                        secondFlip.add(edge)
                    #e = random.choice(candidates)
                    #secondFlip.add(e)
            
        return to_Flip ,secondFlip

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
            if edge in a.possible_flips():
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
    for e in blocked_edges:
        if e not in free_edges and e  not in set_b and e in a_temp.possible_flips():
            try:
                a_dup = a_temp.fork()
                a_dup.add_flip(e)
                a_dup.commit()
                t1, t2 = new_triangles(a,e)
                for triangle in [t1, t2]:
                    for e1 in triangle: 
                       e_norm = normalize_edge(*e1)
                       if isFree(a_dup, set_b, e_norm):
                         free_edges.add(e_norm)

            except ValueError:
                continue
    if not free_edges:       
        for edge in blocked_edges:
            e_norm = normalize_edge(*edge)
            if e_norm in a_temp.possible_flips() and e_norm not in set_b:
                free_edges.add(e_norm)


    if free_edges:
        recursive_score = blocking_edges(a_temp, set_b, free_edges, k - 1)
        score += recursive_score 
    return score


