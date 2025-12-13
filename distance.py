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
        
        setChangedEdges -= toRemove
        setChangedEdges |= toAdd
        lastFlips = setFlips.copy()

        a_working.commit() # we commite the flips in the end
        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist+=1

        if(dist > 250):
            #print(f"250 itertion it too much itteratio we are goin to stop")
            break

    if(dist <= 250):
        print(f"  end distance is {dist}")

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
def blocking_edges(
    a: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    edges: set[tuple[int, int]],
    k: int
) -> int:

    if k == 0:
        return 0

    # אלכסונים חופשיים אמיתיים במצב הנוכחי
    free_edges = {
        e for e in edges
        if e not in set_b
        and e in a.possible_flips()
        and isFree(a, set_b, e)
    }

    # ─────────────────────────────
    # מקרה 1: יש אלכסונים חופשיים
    # ─────────────────────────────
    if free_edges:
        try:
            a_next = a.fork()
            for e in free_edges:
                a_next.add_flip(e)
            a_next.commit()
        except ValueError:
            # fallback – אם לא כולם באמת בלתי תלויים
            best = 0
            for e in free_edges:
                a_tmp = a.fork()
                a_tmp.add_flip(e)
                a_tmp.commit()
                best = max(
                    best,
                    1 + blocking_edges(a_tmp, set_b, set(), k - 1)
                )
            return best

        new_candidates = set()
        for e in free_edges:
            t1, t2 = new_triangles(a_next, e)
            for tri in (t1, t2):
                for e1 in tri:
                    e_norm = normalize_edge(*e1)
                    if e_norm not in set_b:
                        new_candidates.add(e_norm)

        return len(free_edges) + blocking_edges(
            a_next,
            set_b,
            new_candidates,
            k - 1
        )

    # ─────────────────────────────
    # מקרה 2: אין אלכסונים חופשיים
    # ─────────────────────────────
    candidates = {
        e for e in edges
        if e not in set_b and e in a.possible_flips()
    }

    if not candidates:
        return 0

    best = 0

    for subset in maximal_independent_subsets(a, candidates):

        try:
            a_next = a.fork()
            for e in subset:
                a_next.add_flip(e)
            a_next.commit()
        except ValueError:
            continue

        new_candidates = set()
        for e in subset:
            t1, t2 = new_triangles(a_next, e)
            for tri in (t1, t2):
                for e1 in tri:
                    e_norm = normalize_edge(*e1)
                    if e_norm not in set_b:
                        new_candidates.add(e_norm)

        best = max(
            best,
            blocking_edges(
                a_next,
                set_b,
                new_candidates,
                k - 1
            )
        )

    return best
