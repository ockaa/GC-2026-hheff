import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from helpFuncs import normalize_edge , new_triangles,diff,isFree,maximal_independent_subsets
edge_attempt_count = defaultdict(int)
def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    edge_attempt_count.clear()

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
        
        setFlips_h, toRemove_h, toAdd_h ,flips_h = Huristic(a_working, set_b, setChangedEdges, lastFlips, k)
        toRemove |= toRemove_h
        toAdd |= toAdd_h
        setFlips |= setFlips_h
        setFlipsWithPartner |= flips_h
        
        #setChangedEdges -= toRemove
        
        #setChangedEdges |= toAdd
        lastFlips = setFlips.copy()

        a_working.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist+=1
        setChangedEdges = {
            normalize_edge(*e)
            for e in a_working.get_edges()
            if normalize_edge(*e) not in set_b
        }

     #   print("still diff:", len(set(a_working.get_edges()) - set_b))
      
      #  print("changedEdges:", len(setChangedEdges))
        if(dist > 400):
            #print(f"250 itertion it too much itteratio we are goin to stop")
            break

    #if(dist <= 400):
        #print(f"  end distance is {dist}")

    return dist , flips_by_layer , flips_with_partner_by_layer
def Huristic(
    a: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    setChangedEdges: set[tuple[int, int]],
    lastFlips: set[tuple[int, int]],
    k: int
) -> tuple[set, set, set]:  # מחזיר גם toRemove וגם toAdd
       
    edge_by_score = []
    to_Flip = set()
    toRemove = set()
    toAdd = set()
    setFlipsWithPartner = set()
    
    for e in set(setChangedEdges):
        try:
            score = blocking_edges(a, set_b, {e}, k)
            edge_by_score.append((e, score))
        except ValueError:
            continue
    if not edge_by_score:
      return set(), set(), set(), set()

    best_edge, best_score = max(edge_by_score, key=lambda x: x[1])

    for e, score in edge_by_score:
        try:
            flip_rev = normalize_edge(*a.get_flip_partner(e))
            if e in a.possible_flips() and flip_rev not in lastFlips:
                if (score > 0) and e not in set_b:
                    a.add_flip(e) 
                    to_Flip.add(e)
                    toRemove.add(e)
                    toAdd.add(flip_rev)
                    setFlipsWithPartner.add((e,flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
        except ValueError:
            continue
                         
    if best_score == 0 or len(setChangedEdges)> 100:
        candidates = [e for e in setChangedEdges if e not in set_b and e not in lastFlips]
        for e in candidates:
            if edge_attempt_count[e] == 0:
                try:
                    e = random.choice(candidates)
                    flip_rev = normalize_edge(*a.get_flip_partner(e))
                    a.add_flip(e)  
                    to_Flip.add(e)
                    toRemove.add(e)
                    toAdd.add(flip_rev)
                    setFlipsWithPartner.add((e,flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                except:
                    pass

    return to_Flip, toRemove, toAdd ,setFlipsWithPartner
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