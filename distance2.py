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
        
        for e in set(setChangedEdges):
            try: 
                if e in a_working.possible_flips():
                    if (((Huristic(a_working,b,e,giga)) or (blocking_edges(a_working,set_b,e) > 0))and e not in set_b):
                        a_working.add_flip((e))
                        toRemove.add(e)
                        toAdd.add(normalize_edge(*a_working.get_flip_partner(e)))
                        setFlips.add(e)
                        amount+=1
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
