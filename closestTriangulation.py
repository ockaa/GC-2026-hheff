import os
from pathlib import Path
import matplotlib.pyplot as plt
from distance import distance

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
def caculate_all_dis(triangulations: list[FlippableTriangulation]) -> list[list[int]]:
    n = len(triangulations)
    dist = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n): 
            min_d = 40000
            print(f"now caculate for t{i} and t{j}")
            for k in range(5):
                d,_,_ = distance(triangulations[i], triangulations[j])
                if min_d > d:
                    min_d = d
            dist[i][j] = min_d
            dist[j][i] = min_d  

    return dist

def caculate_min_dis(arr: list[int] , n:int) -> int:
    min_i = -1
    for i in range(n):
        if(min_i == -1):
            min_i = i
        elif(arr[i] < arr[min_i]):
            min_i = i
    return min_i

def closestTringulation(
    triangulations: list[FlippableTriangulation],
) -> tuple[int, FlippableTriangulation]:
    n = len(triangulations)
    distance_matrix = caculate_all_dis(triangulations)
    arr = [0] * n
    for i in range(n):
        for j in range(n): 
            arr[i] += distance_matrix[i][j] 
    min_i = caculate_min_dis(arr , n)
    return arr[min_i] , triangulations[min_i] ,distance_matrix

 
