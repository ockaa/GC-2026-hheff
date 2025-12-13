import os
from pathlib import Path
import matplotlib.pyplot as plt
from distance import distance
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from helpFuncs import reconstruct_triangulation_sequence
from c_builder import fromCompToFlips
# ===========================
# פונקציה לחישוב כל המרחקים
# ===========================
def caculate_all_dis(triangulations: list[FlippableTriangulation]) -> list[list[tuple[int,set,set]]]:
    n = len(triangulations)
    dist: list[list[tuple[int,set,set]]] = [[(0,set(),set()) for _ in range(n)] for _ in range(n)]  # <-- שונה

    for i in range(n):
        for j in range(i + 1, n): 
            
            min_distance_result = (0, set(), set())
            print(f"now calculate for t{i} and t{j}")
            min_d = 251
            for k in range(5):
                nd = 251
                while nd == 251:
                    nd,stageflips,l2 = distance(triangulations[i], triangulations[j])
                    if nd < 251:
                        d , s = fromCompToFlips(triangulations[i],stageflips)
                        distance_result = d,s,l2
                        if min_d > d :
                            min_d = d
                            min_distance_result = distance_result
                    


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
def closestTringulation(triangulations: list[FlippableTriangulation], imposter: bool = False) -> tuple[int, FlippableTriangulation, list[list[tuple[int,set,set]]]]:
    """
    מוצא את הטריאנגולציה הקרובה ביותר לכל השאר
    
    Args:
        triangulations: רשימת טריאנגולציות
        imposter: אם True, האיבר האחרון ברשימה הוא imposter ולא נכלל בחישוב הסכום
    """
    n = len(triangulations)
    distance_result_matrix = caculate_all_dis(triangulations)

    arr = [0] * n
    
    if imposter:
        # אם יש imposter, מחשבים את הסכום רק עד n-1 (לא כולל האחרון)
        effective_n = n - 1
        for i in range(n):
            for j in range(effective_n):  # ✅ עד n-1 בלבד
                d, _, _ = distance_result_matrix[i][j]  
                arr[i] += d
    else:
        # במקרה רגיל, מחשבים את הסכום לכולם
        for i in range(n):
            for j in range(n): 
                d, _, _ = distance_result_matrix[i][j]  
                arr[i] += d

    min_i = caculate_min_dis(arr, n)
    return arr[min_i], triangulations[min_i], distance_result_matrix,min_i

#=========================
# חישוב למציאת טרינגולציה הכי קרובה בין רשימת טרינגולצית לטרינגולצית יעד
#=========================

def closest_to_target(triangulations: list[FlippableTriangulation],
                      target: FlippableTriangulation,
                      repeats: int = 5):
    """
    מחזירה את הטריאנגולציה הכי קרובה ל-target
    """

    best_dist = float("inf")
    best_index = -1
    best_triang = None
    distance_results = []

    for i, T in enumerate(triangulations):
        print(f"Checking distance between target and T{i}")

        min_d = float("inf")
        best_result = None

        for _ in range(repeats):
            nd,stageflips,l2 = distance(T, target)
            d , s = fromCompToFlips(T,stageflips)
            distance_result = d,s,l2
            if d < min_d:
                min_d = d
                best_result = distance_result

        distance_results.append(best_result)

        if min_d < best_dist:
            best_dist = min_d
            best_index = i
            best_triang = T

    return best_dist, best_triang, best_index, distance_results



def closest_point_between(A, B, target):
    d, flips, _ = distance(A, B)
    path = reconstruct_triangulation_sequence(A, flips)
    _, best_T, _ ,_= closest_to_target(path, target)
    return best_T


def median_triangulation(triangulations):
    # שלב 0: מתחילים משתי הטריאנגולציות הראשונות
    M = triangulations[0]
    N = triangulations[1]

    # מוצאים טריאנגולציה באמצע בין שתיהן — ביחס אחת לשנייה
    M = closest_point_between(M, N, N)  
    # (זה בעצם אומר: בערך אמצע בין M ל-N)

    # עכשיו עוברים על שאר הטריאנגולציות
    for i in range(2, len(triangulations)):
        T = triangulations[i]

        # 1) בטווח בין M לבין N (העוגן הקודם) —
        #    מי הכי קרובה ל-T?
        candidate = closest_point_between(M, N, T)

        # 2) עכשיו בין M החדש ל-T —
        #    מי הכי טובה לכל הקודמים (שמסומל ב-M)
        M = closest_point_between(candidate, T, M)

        # 3) מעדכנים את N (העוגן הימני) להיות T החדש
        N = T

    return M
