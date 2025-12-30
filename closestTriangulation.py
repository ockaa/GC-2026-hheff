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
    max_num = 401
    for i in range(n):
        for j in range(i + 1, n): 
            
            min_distance_result = (0, set(), set())
            print(f"now calculate for t{i} and t{j}")
            min_d = max_num
            
            for k in range(10):
                nd = max_num
                d = 200
                p =0
                while nd == max_num:
                    nd1,stageflips,l1 = distance(triangulations[i], triangulations[j])
                    nd2,stageflips2,l2 = distance(triangulations[j], triangulations[i])
                    if(nd1<nd2): 
                        nd = nd1
                    else: 
                        nd = nd2
                    if nd < max_num:
                        d1 , s1 = fromCompToFlips(triangulations[i],stageflips)
                        d2 , s2 = fromCompToFlips(triangulations[j],stageflips2)
                        if(d1 < d2):
                            d,s,l = d1,s1,l1
                        else:
                            d,s,l = d2,s2,l2
                        distance_result = d,s,l
                        if min_d > d :
                            min_d = d
                            min_distance_result = distance_result
                        print(f"  found length : {d}")
                    p+=1
                    if p > 30 and min_d < 23:
                        print("  * took to long skip")
                        break
                    if p > 100:
                        distance_result = d,s,l
                        min_distance_result = distance_result
                        print("  * couldent find distance")
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
        print(f" {i+1}.Checking distance between target and T{i}")

        min_d = float("inf")
        best_result = None

        for k in range(repeats):
            nd1,stageflips,l1 = distance(T, target)
            nd2,stageflips2,l2 = distance(target,T)
            if(nd1<nd2): 
                nd = nd1
            else: 
                nd = nd2
            
            d1 , s1 = fromCompToFlips(T,stageflips)
            d2 , s2 = fromCompToFlips(target,stageflips2)
            if(d1 < d2):
                d,s,l = d1,s1,l1
            else:
                d,s,l = d2,s2,l2
            distance_result = d,s,l
            print(f"   {k+1}.found length : {d}")
            if min_d > d :
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
        print(f"Adding new trag : T{i}")
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
