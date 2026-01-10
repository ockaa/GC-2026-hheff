import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict, deque
import networkx as nx
from itertools import chain
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from helpFuncs import normalize_edge , new_triangles,diff,isFree,maximal_independent_subsets


edge_attempt_count = defaultdict(int)

# =========================================================
# 1. Separator מישורי (ליפטון–טארג'ן על גרף קשתות משותפות)
# =========================================================

def find_barrier_path_fast(shared_edges, max_time_ms=200):
    """
    מחזיר שכבת BFS שמפרידה את גרף הקשתות המשותפות בערך לחצי
    (Separator מישורי)
    """
    if not shared_edges:
        return None

    point_to_edges = defaultdict(list)
    for e in shared_edges:
        for p in e:
            point_to_edges[p].append(e)

    adj = defaultdict(set)
    for edges in point_to_edges.values():
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                adj[edges[i]].add(edges[j])
                adj[edges[j]].add(edges[i])

    start = next(iter(shared_edges))
    level = {start: 0}
    q = deque([start])
    layers = defaultdict(list)

    while q:
        u = q.popleft()
        layers[level[u]].append(u)
        for v in adj[u]:
            if v not in level:
                level[v] = level[u] + 1
                q.append(v)

    total = len(shared_edges)
    seen = 0
    for i in sorted(layers):
        seen += len(layers[i])
        if total / 3 <= seen <= 2 * total / 3:
            return set(layers[i])

    return None


# =========================================================
# 2. חלוקה לרכיבים קשירים אחרי הסרת המחסום
# =========================================================

def split_by_connected_components(T, barrier_edges):
    all_edges = set(normalize_edge(*e) for e in T.get_edges())
    barrier = set(barrier_edges)
    remaining = all_edges - barrier

    if not remaining:
        return None, None

    point_to_edges = defaultdict(list)
    for e in remaining:
        for p in e:
            point_to_edges[p].append(e)

    adj = defaultdict(set)
    for edges in point_to_edges.values():
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                adj[edges[i]].add(edges[j])
                adj[edges[j]].add(edges[i])

    components = []
    visited = set()

    for e in remaining:
        if e in visited:
            continue
        comp = set()
        q = deque([e])
        visited.add(e)
        while q:
            u = q.popleft()
            comp.add(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        components.append(comp)

    if len(components) != 2:
        return None, None

    return (
        components[0] | barrier,
        components[1] | barrier
    )


# =========================================================
# 3. תנאי מתי שווה לנסות לחלק
# =========================================================

def should_split_triangulation(T1, T2, shared_edges):
    total_edges = len(list(T1.get_edges()))
    if total_edges < 300:
        return False
    if len(shared_edges) < 150:
        return False
    return True


# =========================================================
# 4. distance עם ניסיון חלוקה
# =========================================================

def distance_with_split(T1, T2, distance_func):
    list_T1 = set(normalize_edge(*e) for e in T1.get_edges())
    list_T2 = set(normalize_edge(*e) for e in T2.get_edges())
    shared_edges = list_T1 & list_T2

    print("\n=== Split Analysis ===")
    print(f"Total edges: {len(list_T1)}")
    print(f"Shared edges: {len(shared_edges)}")

    if not should_split_triangulation(T1, T2, shared_edges):
        print("→ NOT splitting")
        return distance_func(T1, T2)

    print("→ Searching separator...")
    barrier = find_barrier_path_fast(shared_edges)

    if barrier is None:
        print("→ No separator found")
        return distance_func(T1, T2)

    T1_l, T1_r = split_by_connected_components(T1, barrier)
    T2_l, T2_r = split_by_connected_components(T2, barrier)

    if T1_l is None or T2_l is None:
        print("→ Split failed")
        return distance_func(T1, T2)

    print(f"✓ Split success: {len(T1_l)} | {len(T1_r)}")

    pts = T1._flip_map.points

    try:
        TL1 = FlippableTriangulation.from_points_edges(pts, list(T1_l))
        TR1 = FlippableTriangulation.from_points_edges(pts, list(T1_r))
        TL2 = FlippableTriangulation.from_points_edges(pts, list(T2_l))
        TR2 = FlippableTriangulation.from_points_edges(pts, list(T2_r))

        d1, f1, p1 = distance_func(TL1, TL2)
        d2, f2, p2 = distance_func(TR1, TR2)

        return d1 + d2, f1 + f2, p1 + p2

    except Exception as e:
        print("→ Fallback:", e)
        return distance_func(T1, T2)


# =========================================================
# 5. distance מהיר (active edges)
# =========================================================

def distance_optimized(a: FlippableTriangulation,
                       b: FlippableTriangulation):

    edge_attempt_count.clear()
    k = 16
    dist = 0
    flips_by_layer = []
    flips_with_partner_by_layer = []

    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    set_b = set(listb)

    a_working = a.fork()
    lastFlips = set()

    setChangedEdges = set(diff(lista, listb))
    active_edges = setChangedEdges.copy()

    while not a_working.__eq__(b):
        if dist > 400:
            break

        setFlips = set()
        setFlipsWithPartner = set()
        new_active = set()

        for e in list(active_edges):
            if e not in setChangedEdges:
                continue
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    new_active.add(flip_rev)
            except ValueError:
                continue

        h_flips, h_pairs, h_active = Heuristic_optimized(
            a_working, set_b, active_edges, setChangedEdges, lastFlips, k
        )

        setFlips |= h_flips
        setFlipsWithPartner |= h_pairs
        new_active |= h_active

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

        if len(setChangedEdges) < 50:
            active_edges = setChangedEdges.copy()
        else:
            active_edges = new_active & setChangedEdges

    return dist, flips_by_layer, flips_with_partner_by_layer


# =========================================================
# 6. Heuristic מתוקן (אין יותר None!)
# =========================================================

def Heuristic_optimized(a, set_b, active_edges, setChangedEdges, lastFlips, k):
    edge_by_score = []
    to_Flip = set()
    setFlipsWithPartner = set()
    new_active = set()

    edges_to_check = active_edges & setChangedEdges

    for e in edges_to_check:
        try:
            score = blocking_edges(a, set_b, {e}, k)
            if score is not None:
                edge_by_score.append((e, score))
        except ValueError:
            continue

    if not edge_by_score:
        return set(), set(), set()

    best_edge, best_score = max(edge_by_score, key=lambda x: x[1])

    for e, score in edge_by_score:
        if score <= 0 or e in lastFlips or e in set_b:
            continue
        try:
            flip_rev = normalize_edge(*a.get_flip_partner(e))
            if e in a.possible_flips():
                a.add_flip(e)
                to_Flip.add(e)
                setFlipsWithPartner.add((e, flip_rev))
                new_active.add(flip_rev)
        except ValueError:
            pass

    return to_Flip, setFlipsWithPartner, new_active


# =========================================================
# 7. הפונקציה הראשית
# =========================================================

def distance_super_optimized(T1, T2):
    return distance_with_split(T1, T2, distance_optimized)


# =========================================================
# 8. blocking_edges – נשאר שלך
# =========================================================

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
# ===========================
# דוגמה לשימוש
# ===========================

"""
# במקום:
d, flips, partner = distance(T1, T2)

# השתמשי ב:
d, flips, partner = distance_super_optimized(T1, T2)

# זה יעשה:
# 1. ינסה לחלק לשתי טריאנגולציות (אם יש הרבה צלעות משותפות)
# 2. אם הצליח - ירוץ distance_optimized על כל חצי בנפרד
# 3. אם לא הצליח - ירוץ distance_optimized רגיל
"""