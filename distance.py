import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
def distance(
    a: FlippableTriangulation,
    b: FlippableTriangulation
) -> tuple[int, list[list[tuple[int, int]]]]:
    dist =0
    flips_by_layer = list()
    lista = a.get_edges()
    listb = b.get_edges()
    set_b = set(listb)
    setChangedEdges = set(diff(lista, listb))
    while a!=b:
        setFlips = set()
        amount = 0
        for u, v in set(setChangedEdges): #we flip all edges that are final in b
            try:
                flipped_edge = a.get_flip_partner((u, v))
                flipped_edge_reverse = (flipped_edge[1], flipped_edge[0])
                if flipped_edge in set_b or flipped_edge_reverse in set_b:
                    a.add_flip((u, v))
                    setChangedEdges.remove((u, v))
                    setFlips.add((u,v))
            except ValueError:
                continue
        setflipable = set(a.possible_flips())
        for u,v in set(setChangedEdges): #flip some edges (that can be fliped) in some way
            try:
                if Huristic(a,b,u,v):
                    a.add_flip((u,v))
                    #remove the edge we flipped from out list an add the fliped edge
                    setChangedEdges.remove((u,v))
                    setChangedEdges.add((a.get_flip_partner((u,v))))
                    #update the flipable edges
                    setflipable = set(a.possible_flips())
                    setFlips.add((u,v))
                    amount+=1
            except ValueError:
                continue
        
        
        a.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        dist+=1

        print(f"{amount}")
        print(setChangedEdges)


    return dist , flips_by_layer


def Huristic(
    a: FlippableTriangulation,
    b: FlippableTriangulation,
    u,v: tuple[int, int]
) -> bool:
    
    if random.random() < 0.5:
        return True
    else:
        return False
    

def diff(a: list[tuple[int, int]] , b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    set_a = set(a)
    set_b = set(b)
    symmetric_diff = set_a.symmetric_difference(set_b)
    return list(symmetric_diff)
