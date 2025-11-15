import os
from pathlib import Path
import matplotlib.pyplot as plt

from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance


INSTANCE_FOLDER = "benchmark_instances"
INSTANCE_FILENAME = "random_instance_4_40_2.json" 

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

    # Create the list of Point objects (the essential fix)
    points_list = [
        Point(x, y) 
        for x, y in zip(instance.points_x, instance.points_y)
    ]
    
    # 2. Setup Plotting for All Triangulations
    print("\n--- 2. Setting up Plotting ---")
    
    colums = num_triangulations
    rows = 1
    # Simple layout: one row, N columns
    fig, axes = plt.subplots(
        rows, colums, 
        figsize=(4 * num_triangulations, 5) # Adjust figure size based on count
    )

    # Ensure 'axes' is an iterable array even if there is only one plot
    if num_triangulations == 1:
        axes = [axes]

    # 3. Iterate and Plot Each Triangulation
    print("--- 3. Plotting Each Triangulation ---")
    
    for i, initial_edges in enumerate(instance.triangulations):
        ax = axes[i]
        try:
            tri = FlippableTriangulation.from_points_edges(points_list, initial_edges)
            all_edges = tri.get_edges()
        except Exception as e:
            print(f"Could not initialize Triangulation {i}: {e}. Skipping plot.")
            ax.set_title(f"Triangulation {i} (Error)")
            continue

        # Plot the edges
        draw_edges(
            points_list, 
            all_edges, 
            ax=ax, 
            show_indices=True
        )
        
        # Set titles and formatting
        ax.set_title(f"Triangulation {i}\n({len(initial_edges)} Interior Edges)")
        ax.set_aspect('equal', adjustable='box') 
        
    # Finalize and show plot
    fig.suptitle(f"All Triangulations for Instance: {instance.instance_uid}", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95]) # Adjust layout to make room for suptitle
    print("Displaying plot...")
    plt.show()

if __name__ == "__main__":
    main()