from math import dist
import os
from pathlib import Path
import matplotlib.pyplot as plt
from c_builder import fromCompToFlips
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from drawing import Draw_distance, Draw_Manager_Components ,Draw_triangulation
from distance import distance
from c_builder import ConnectedDirectedComponent, DynamicGraphManager, MakeComponents
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_881_320_10.json" 

def main():
    # 1. Locate and Load the Instance
    print("--- 1. Loading Instance ---")
    
    script_dir = Path(__file__).parent
    instance_path = script_dir / INSTANCE_FOLDER / INSTANCE_FILENAME
    
    if not instance_path.exists():
        print(f"Error: Instance file not found at {instance_path}")
        return

    try:
        instance: CGSHOP2026Instance = read_instance(str(instance_path))
        num_triangulations = len(instance.triangulations)
        print(f"Loaded instance '{instance.instance_uid}' with {len(instance.points_x)} points and {num_triangulations} triangulations.")
        
    except Exception as e:
        print(f"Error reading instance file: {e}")
        return

    points_list = [
        Point(x, y) 
        for x, y in zip(instance.points_x, instance.points_y)
    ]
    n = len(instance.triangulations)
   
    for one in range(n):
        for two in range(one + 1, n): 
            print(f"check for t{one} and t{two}")
            triang1 = instance.triangulations[one]
            triang2 = instance.triangulations[two]
            a: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang1)
            b: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang2)
            


            a_clone = a.fork()
            points_coords = [(p.x(), p.y()) for p in a._flip_map.points]
            
            
            """draw_triangulation(
                points_coords, 
                a_clone.get_edges()
            )"""
            dist = 251
            while dist > 250:
                dist,stages_of_flips,l2 = distance(a.fork(),b.fork())
            stages_of_flips_comp = list(list())
            #print(f"Distance between triangulations before comp: {dist}")

            # Create a worker copy so we don't modify the original 'a'
            a_working = a.fork()    
            """
            for i, stage in enumerate(stages_of_flips):
                print(f"\n--- Stage {i} ---")
                
                for edge in stage:
                    # add_flip returns the NEW edge that was created
                    try:
                        created_edge = a_working.add_flip(edge)
                        print(f"  Flipped {edge}  -->  Created {created_edge}")
                    except ValueError as e:
                        print(f"  main Failed to flip {edge}: {e}")
                    
                # Commit the changes for this stage before moving to the next
                a_working.commit()"""
            a_clone2 = a.fork()
            
            dist_comp , global_layers = fromCompToFlips(a,stages_of_flips)
            print(f"  new dist : {dist_comp}")
            for i, layer in enumerate(global_layers):
                # print(f"Processing Global Layer {i} with {len(layer)} flips...")
                stages_of_flips_comp.append(list())
                
                for node_id in layer:
                    # node_id is (Edge_Before, Edge_After, ID)
                    edge_to_flip = node_id[0]
                    
                    try:
                        a_clone2.add_flip(edge_to_flip)
                        # FIX: Use 'i' (the index) instead of 'layer' (the list object)
                        stages_of_flips_comp[i].append(edge_to_flip) 
                    except ValueError:
                        # This catches edges that might conflict within the same batch
                        # (Though topological sort usually prevents this for dependencies)
                        pass
                
                # Commit AFTER processing the full layer (All components advance together)
                a_clone2.commit()
            if(not a_clone2.__eq__(b)):
                print(f"do the flips lead to b: {a_clone2.__eq__(b)}")
            Draw_distance(dist_comp, stages_of_flips_comp, a,b,points_list)
            #Draw_Manager_Components(manager)
if __name__ == "__main__":
    main()