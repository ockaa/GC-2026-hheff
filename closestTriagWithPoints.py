import os
from pathlib import Path
import matplotlib.pyplot as plt
from distance import distance
from try_distance import distance_super_optimized
import math

from itertools import combinations
import random
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from helpFuncs import reconstruct_triangulation_sequence,is_ending_right
from c_builder import fromCompToFlips

# ===========================
# פרמטר גלובלי לחזרות
# ===========================
repeats = 5

# ===========================
# פונקציה לחישוב כל המרחקים
# ===========================
def caculate_all_dis(triangulations: list[FlippableTriangulation], points_list) -> list[list[tuple[int,set,set]]]:
    n = len(triangulations)
    dist: list[list[tuple[int,set,set]]] = [[(0,set(),set()) for _ in range(n)] for _ in range(n)]
    max_num = 401
    for i in range(n):
        for j in range(i + 1, n): 
            min_distance_result = (0, set(), set())
            print(f"now calculate for t{i} and t{j}")
            min_d = max_num
            for k in range(repeats):
                nd = max_num
                d = 200
                p = 0
                while nd == max_num:
                    nd1, stageflips, l1 = distance_super_optimized(triangulations[i], triangulations[j], points_list)
                    nd2, stageflips2, l2 = distance_super_optimized(triangulations[j], triangulations[i], points_list)
                    nd = min(nd1, nd2)
                    if nd < max_num:
                        d1, s1 = fromCompToFlips(triangulations[i], stageflips)
                        d2, s2 = fromCompToFlips(triangulations[j], stageflips2)
                        if d1 < d2:
                            d, s, l = d1, s1, l1
                            print(f"a with stage flips is b :{is_ending_right(triangulations[i], triangulations[j], s)}")
                        else:
                            d, s, l = d2, s2, l2
                            print(f"a with stage flips is b :{is_ending_right(triangulations[j], triangulations[i], s)}")
                        distance_result = d, s, l
                        if min_d > d:
                            min_d = d
                            min_distance_result = distance_result
                        print(f"  found length : {d}")
                    p += 1
                    if p > 30 and min_d < 23:
                        print("  * took too long skip")
                        break
                    if p > 100:
                        distance_result = d, s, l
                        min_distance_result = distance_result
                        print("  * couldn't find distance")
                        break
            print(f"  {k+1}.found min : {min_d}")
            dist[i][j] = min_distance_result  
            dist[j][i] = min_distance_result  
        dist[i][i] = (0, set(), set())
    return dist

# ===========================
# פונקציה למציאת אינדקס המינימום
# ===========================
def caculate_min_dis(arr: list[int], n: int) -> int:
    min_i = -1
    for i in range(n):
        if min_i == -1 or arr[i] < arr[min_i]:
            min_i = i
    return min_i

# ===========================
# פונקציה למציאת ה-triangulation הקרוב ביותר
# ===========================
def closestTringulation(triangulations: list[FlippableTriangulation], points_list, imposter: bool = False) -> tuple[int, FlippableTriangulation, list[list[tuple[int,set,set]]], int]:
    n = len(triangulations)
    distance_result_matrix = caculate_all_dis(triangulations, points_list)

    arr = [0] * n
    effective_n = n - 1 if imposter else n
    for i in range(n):
        for j in range(effective_n):
            d, _, _ = distance_result_matrix[i][j]
            arr[i] += d
    min_i = caculate_min_dis(arr, n)
    return arr[min_i], triangulations[min_i], distance_result_matrix, min_i

# ===========================
# פונקציה למציאת הטריאנגולציה הקרובה ביותר ליעד
# ===========================
def closest_to_target(triangulations: list[FlippableTriangulation],
                      target: FlippableTriangulation,
                      points_list,
                      repeats: int = repeats):
    best_dist = float("inf")
    best_index = -1
    best_triang = None
    distance_results = []

    for i, T in enumerate(triangulations):
        print(f" {i+1}.Checking distance between target and T{i}")
        min_d = float("inf")
        best_result = None
        for k in range(repeats):
            nd1, stageflips, l1 = distance_super_optimized(T, target, points_list)
            nd2, stageflips2, l2 = distance_super_optimized(target, T, points_list)
            nd = min(nd1, nd2)
            d1, s1 = fromCompToFlips(T, stageflips)
            d2, s2 = fromCompToFlips(target, stageflips2)
            if d1 < d2:
                d, s, l = d1, s1, l1
            else:
                d, s, l = d2, s2, l2
            distance_result = d, s, l
            print(f"   {k+1}.found length : {d}")
            if min_d > d:
                min_d = d
                best_result = distance_result
        print(f"   found min : {min_d}")
        distance_results.append(best_result)
        if min_d < best_dist:
            best_dist = min_d
            best_index = i
            best_triang = T
    print(f" found min : {best_dist}")
    return best_dist, best_triang, best_index, distance_results

# ===========================
# פונקציה למציאת נקודה קרובה בין שני טריאנגולציות
# ===========================
def closest_point_between(A, B, target, points_list, max_candidates=30):
    d, flips, _ = distance(A, B)
    path = reconstruct_triangulation_sequence(A, flips)
    if len(path) == 0:
        return A
    if len(path) <= max_candidates:
        _, best_T, _, _ = closest_to_target(path, target, points_list)
        return best_T
    step = math.ceil(len(path) / max_candidates)
    reduced_path = path[::step]
    if len(reduced_path) == 0:
        reduced_path = [path[0]]
    _, best_T, _, _ = closest_to_target(reduced_path, target, points_list)
    return best_T

# ===========================
# חישוב טריאנגולציה חציונית
# ===========================
def median_triangulation_2(triangulations, points_list):
    M = triangulations[0]
    N = triangulations[1]
    M = closest_point_between(M, N, N, points_list)
    for i in range(2, len(triangulations)):
        T = triangulations[i]
        candidate = closest_point_between(M, N, T, points_list)
        M = closest_point_between(candidate, T, M, points_list)
        N = T
    return M

# ===========================
# סכום המרחקים לסט המקורי
# ===========================
def total_distance(T: FlippableTriangulation, originals: list[FlippableTriangulation], points_list) -> int:
    return sum(distance(T, S)[0] for S in originals)

# ===========================
# זוג הכי רחוק בסט
# ===========================
def farthest_pair(triangulations: list[FlippableTriangulation], points_list) -> tuple[int,int]:
    max_d = -1
    pair = (0, 1)
    n = len(triangulations)
    for i in range(n):
        for j in range(i + 1, n):
            d, _, _ = distance(triangulations[i], triangulations[j])
            if d > max_d:
                max_d = d
                pair = (i, j)
    return pair

# ===========================
# מנסה להחליף זוג ב-midpoint
# ===========================
def try_replace_pair(triangulations: list[FlippableTriangulation], originals: list[FlippableTriangulation], points_list) -> bool:
    i, j = farthest_pair(triangulations, points_list)
    T1, T2 = triangulations[i], triangulations[j]
    mid = closest_point_between(T1, T2, T2, points_list)
    score_mid = total_distance(mid, originals, points_list)
    score_1 = total_distance(T1, originals, points_list)
    score_2 = total_distance(T2, originals, points_list)
    if score_mid < min(score_1, score_2):
        if score_1 > score_2:
            triangulations[i] = mid
        else:
            triangulations[j] = mid
        return True
    return False

# ===========================
# כיווץ סט טריאנגולציות
# ===========================
def contract_triangulations(triangulations: list[FlippableTriangulation], points_list, max_iters: int = 20) -> list[FlippableTriangulation]:
    originals = triangulations[:]
    S = triangulations[:]
    for _ in range(max_iters):
        improved = try_replace_pair(S, originals, points_list)
        if not improved:
            break
    return S

# ===========================
# מציאת המרכז הסופי
# ===========================
def find_center(triangulations: list[FlippableTriangulation], points_list) -> FlippableTriangulation:
    best_T = None
    best_score = float('inf')
    for T in triangulations:
        s = total_distance(T, triangulations, points_list)
        if s < best_score:
            best_score = s
            best_T = T
    return best_T

# ===========================
# האלגוריתם הדינמי המלא
# ===========================
def dynamic_median_triangulation(original_triangulations: list[FlippableTriangulation], points_list) -> FlippableTriangulation:
    reduced_set = contract_triangulations(original_triangulations, points_list)
    center = find_center(reduced_set, points_list)
    return center
