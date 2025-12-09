from math import dist
import os
from pathlib import Path
import matplotlib.pyplot as plt

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
from drawing import Draw_distance, Draw_Manager_Components ,draw_triangulation
from distance import distance
from c_builder import ConnectedDirectedComponent, DynamicGraphManager, MakeComponents
INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "woc-205-tsplib-8058c7cb.json" 

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
    triang1 = instance.triangulations[0]
    triang2 = instance.triangulations[1]
    a: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang1)
    b: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_list, triang2)
    


    a_clone = a.fork()
    points_coords = [(p.x(), p.y()) for p in a._flip_map.points]

    
    draw_triangulation(
        points_coords, 
        a_clone.get_edges()
    )
    dist,stages_of_flips,l2 = distance(a.fork(),b.fork())
    
    print(f"Distance between triangulations: {dist}")

    # Create a worker copy so we don't modify the original 'a'
    a_working = a.fork()    

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
        a_working.commit()
    a_clone2 = a.fork()
    manager = MakeComponents(a, stages_of_flips)
    
    # 1. Gather all layers from all components into a single 'Global' list of layers
    # global_layers[0] will hold Layer 0 from Comp A, Layer 0 from Comp B, etc.
    global_layers = []

    for comp in manager.get_all_components():
        comp_layers = comp.get_layers_topological()
        
        for depth, layer in enumerate(comp_layers):
            # Ensure the global list is deep enough
            while len(global_layers) <= depth:
                global_layers.append([])
            
            # Merge this component's layer into the global layer at the same depth
            global_layers[depth].extend(layer)

    # 2. Execute the Global Layers sequentially
    print(f"Total parallel stages: {len(global_layers)}")
    
    for i, layer in enumerate(global_layers):
        # print(f"Processing Global Layer {i} with {len(layer)} flips...")
        
        for node_id in layer:
            # node_id is (Edge_Before, Edge_After, ID)
            edge_to_flip = node_id[0]
            
            try:
                a_clone2.add_flip(edge_to_flip)
            except ValueError:
                # This catches edges that might conflict within the same batch
                # (Though topological sort usually prevents this for dependencies)
                pass
        
        # Commit AFTER processing the full layer (All components advance together)
        a_clone2.commit()
    print(f"is {a_clone2.__eq__(b)}")
    Draw_distance(dist, stages_of_flips, a,b,points_list)
    Draw_Manager_Components(manager)
if __name__ == "__main__":
    main()