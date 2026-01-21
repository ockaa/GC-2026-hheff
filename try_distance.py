import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import defaultdict, deque
import networkx as nx
from itertools import chain
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from helpFuncs import normalize_edge, new_triangles, diff, isFree, maximal_independent_subsets


edge_attempt_count = defaultdict(int)

# =========================================================
# 1. Separator מישורי (ליפטון–טארג'ן על גרף קשתות משותפות)
# =========================================================

def find_barrier_path_fast(shared_edges, max_time_ms=200):
    """
    מחזיר שכבת BFS שמפרידה את גרף הקשתות המשותפות בערך לחצי
    """
    if not shared_edges or len(shared_edges) < 50:
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

    # בדיקה שהגרף קשיר
    if not adj:
        return None
    
    start = next(iter(shared_edges))
    visited = {start}
    queue = deque([start])
    
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    
    # אם הגרף לא קשיר, אי אפשר למצוא separator
    if len(visited) < len(shared_edges):
        return None

    # BFS לחיפוש separator
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
# 3. בדיקה אם כדאי לנסות לחלק
# =========================================================

def should_try_split(total_edges, shared_edges_count, layer_num):
    """
    מחליט אם כדאי לנסות לחלק בשכבה הנוכחית
    """
    # אל תנסה בשכבות הראשונות - גרף עדיין לא קשיר
    if layer_num < 5:
        return False
    
    # צריך מספיק קשתות משותפות
    if shared_edges_count < 150:
        return False
    
    # צריך שהטריאנגולציה תהיה מספיק גדולה
    if total_edges < 500:
        return False
    
    # נסה כל 15 שכבות (לא בכל שכבה כי זה יקר)
    if layer_num % 15 != 0:
        return False
    
    return True


# =========================================================
# 4. distance עם בדיקת split דינמית
# =========================================================

def distance_with_dynamic_split(a: FlippableTriangulation,
                                 b: FlippableTriangulation):
    """
    מריץ distance רגיל, אבל אחרי כל כמה שכבות בודק אם אפשר לחלק
    """
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

    while not a_working.__eq__(b):
        if dist > 400:
            break

        # בדיקה אם כדאי לנסות split - רק אם יש עוד הרבה עבודה
        current_changed = len(setChangedEdges)
        
        # אל תנסה split אם כמעט סיימנו
        if current_changed > 50:
            current_shared = set(normalize_edge(*e) for e in a_working.get_edges()) & set_b
            total_edges = len(list(a_working.get_edges()))
            
            if should_try_split(total_edges, len(current_shared), dist):
                print(f"\n=== Layer {dist}: Attempting split ===")
                print(f"Total edges: {total_edges}, Shared: {len(current_shared)}, Changed: {current_changed}")
                
                barrier = find_barrier_path_fast(current_shared)
                
                if barrier is not None:
                    T1_l, T1_r = split_by_connected_components(a_working, barrier)
                    T2_l, T2_r = split_by_connected_components(b, barrier)
                    
                    if T1_l is not None and T2_l is not None:
                        print(f"✓ Split successful! Sizes: {len(T1_l)} | {len(T1_r)}")
                        
                        try:
                            pts = a_working._flip_map.points
                            TL1 = FlippableTriangulation.from_points_edges(pts, list(T1_l))
                            TR1 = FlippableTriangulation.from_points_edges(pts, list(T1_r))
                            TL2 = FlippableTriangulation.from_points_edges(pts, list(T2_l))
                            TR2 = FlippableTriangulation.from_points_edges(pts, list(T2_r))
                            
                            # רקורסיה על שני החצאים
                            d1, f1, p1 = distance_with_dynamic_split(TL1, TL2)
                            d2, f2, p2 = distance_with_dynamic_split(TR1, TR2)
                            
                            # הוספת המרחק שכבר עברנו
                            total_dist = dist + d1 + d2
                            total_flips = flips_by_layer + f1 + f2
                            total_partners = flips_with_partner_by_layer + p1 + p2
                            
                            print(f"✓ Total distance: {dist} (before split) + {d1} + {d2} = {total_dist}")
                            # *** חשוב: return כאן כדי לא להמשיך את הלולאה! ***
                            return total_dist, total_flips, total_partners
                            
                        except Exception as e:
                            print(f"→ Split failed during construction: {e}")
                    else:
                        print(f"→ Split failed: couldn't separate into 2 components")
                else:
                    print(f"→ No separator found (graph not connected yet)")

        # ===== שכבה רגילה - זה החלק שהיה חסר! =====
        setFlips = set()
        setFlipsWithPartner = set()
        toRemove = set()
        toAdd = set()

        # הפיכות חופשיות
        for e in set(setChangedEdges):
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
            except ValueError:
                continue

        # Heuristic
        setFlips_h, toRemove_h, toAdd_h, flips_h = Huristic(
            a_working, set_b, setChangedEdges, lastFlips, k
        )
        toRemove |= toRemove_h
        toAdd |= toAdd_h
        setFlips |= setFlips_h
        setFlipsWithPartner |= flips_h

        lastFlips = setFlips.copy()
        a_working.commit()

        flips_by_layer.append(setFlips)
        flips_with_partner_by_layer.append(setFlipsWithPartner)
        dist += 1

        # עדכון setChangedEdges
        setChangedEdges = {
            normalize_edge(*e)
            for e in a_working.get_edges()
            if normalize_edge(*e) not in set_b
        }

    return dist, flips_by_layer, flips_with_partner_by_layer


# =========================================================
# 5. Huristic
# =========================================================

def Huristic(
    a: FlippableTriangulation,
    set_b: set[tuple[int, int]],
    setChangedEdges: set[tuple[int, int]],
    lastFlips: set[tuple[int, int]],
    k: int
) -> tuple[set, set, set, set]:
       
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
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
        except ValueError:
            continue
                         
    if best_score == 0 or len(setChangedEdges) > 100:
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
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
                except:
                    pass

    return to_Flip, toRemove, toAdd, setFlipsWithPartner


# =========================================================
# 6. blocking_edges
# =========================================================

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
        if e not in free_edges and e not in set_b and e in a_temp.possible_flips():
            try:
                a_dup = a_temp.fork()
                a_dup.add_flip(e)
                a_dup.commit()
                t1, t2 = new_triangles(a, e)
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


# =========================================================
# 7. הפונקציה הראשית
# =========================================================

def distance_super_optimized(T1, T2):
    """
    גרסה משופרת שבודקת separator דינמית אחרי כל כמה שכבות
    """
    return distance_with_dynamic_split(T1, T2)


# =========================================================
# 8. distance רגיל (לשימוש ישיר)
# =========================================================

def distance(a: FlippableTriangulation,
             b: FlippableTriangulation):
    """
    הגרסה המקורית שלך - ללא split
    """
    edge_attempt_count.clear()

    k = 16
    dist = 0
    flips_by_layer = list()
    flips_with_partner_by_layer = list()
    lista = [normalize_edge(*e) for e in a.get_edges()]
    listb = [normalize_edge(*e) for e in b.get_edges()]
    lastFlips = set()

    set_b = set(listb)
    a_working = a.fork()
    setChangedEdges = set(normalize_edge(*e) for e in diff(lista, listb))
    
    while not a_working.__eq__(b):
        setFlips = set()
        setFlipsWithPartner = set()
        toRemove = set()
        toAdd = set()
        
        for e in set(setChangedEdges):
            try:
                if isFree(a_working, set_b, e):
                    flip_rev = normalize_edge(*a_working.get_flip_partner(e))
                    a_working.add_flip(e)
                    toRemove.add(e)
                    setFlips.add(e)
                    setFlipsWithPartner.add((e, flip_rev))
                    edge_attempt_count[flip_rev] = 1 + edge_attempt_count[e]
            except ValueError:
                continue
        
        setFlips_h, toRemove_h, toAdd_h, flips_h = Huristic(
            a_working, set_b, setChangedEdges, lastFlips, k
        )
        toRemove |= toRemove_h
        toAdd |= toAdd_h
        setFlips |= setFlips_h
        setFlipsWithPartner |= flips_h
        
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

        if dist > 400:
            break

    return dist, flips_by_layer, flips_with_partner_by_layer


# ===========================
# דוגמה לשימוש
# ===========================

"""
# עם split דינמי:
d, flips, partner = distance_super_optimized(T1, T2)

# בלי split (המקורי שלך):
d, flips, partner = distance(T1, T2)
"""