import matplotlib.pyplot as plt
import math
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_flips 

def Draw_distance(dist: int,
                  stages_of_flips: list[list[tuple[int, int]]],
                  a: FlippableTriangulation,
                  b: FlippableTriangulation,
                  points_):

    print(f"the distance is: {dist}")

    # --- Pre-calculations ---
    edges_b = set(b.get_edges())
    edges_a_original = set(a.get_edges())
    different_edges_a = edges_a_original.difference(edges_b)
    different_edges_b = edges_b.difference(edges_a_original)

    # --- Window 1: Original vs. Target ---
    fig1, axes1 = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

    # Plot 'a'
    draw_flips(a, show_indices=True, ax=axes1[0])
    for u, v in different_edges_a:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes1[0].plot(x, y, color='red', linewidth=2)
    axes1[0].set_title(f"Triangulation 1 (Original 'a')\n{len(different_edges_a)} edges differ")

    # Plot 'b'
    draw_flips(b, show_indices=True, ax=axes1[1])
    for u, v in different_edges_b:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes1[1].plot(x, y, color='red', linewidth=2)
    axes1[1].set_title(f"Triangulation 2 (Target 'b')\n{len(different_edges_b)} edges differ")


    # --- Window 2: Flip Sequence (Last 5 Steps) ---
    print("--- Creating Window 2: Flip Sequence ---")
    
    # 1. Determine Start Index
    total_stages_count = len(stages_of_flips)
    start_index = max(0, total_stages_count - 1)
    
    # 2. Get the specific stages we want to plot
    stages_to_plot = stages_of_flips[start_index:]
    num_stages_to_plot = len(stages_to_plot)
    total_plots = num_stages_to_plot + 1 # +1 for the state BEFORE the last 5 flips
    
    # 3. Fast-Forward a_tracker to the correct starting state
    a_tracker = a.fork()
    # Apply all flips that happen BEFORE our start_index invisibly
    for stage in stages_of_flips[:start_index]:
        for edge in stage:
            try:
                a_tracker.add_flip(edge)
            except ValueError:
                pass
        a_tracker.commit()

    # 4. Setup Grid
    ncols = 3 # 3 columns is usually good for 6 plots
    nrows = math.ceil(total_plots / ncols)
    
    fig2, axes2 = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, nrows * 6)) 
    axes2_flat = axes2.flat
    fig2.subplots_adjust(hspace=0.4, wspace=0.3)

    # 5. Plot the "Start" State (which is actually state at dist-5)
    current_edges_a = set(a_tracker.get_edges())
    diff_start = current_edges_a.difference(edges_b)
    
    draw_flips(a_tracker, show_indices=False, ax=axes2_flat[0]) 
    for u, v in diff_start:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes2_flat[0].plot(x, y, color='red', linewidth=2)
    
    axes2_flat[0].set_title(f"State at Step {start_index}\n{len(diff_start)} edges differ")
    axes2_flat[0].tick_params(axis='both', which='major', labelsize=8)

    # 6. Loop through the *sliced* stages
    for i, flips_in_this_stage in enumerate(stages_to_plot):
        plot_index = i + 1
        real_stage_number = start_index + i + 1

        # Apply flips
        for edge in flips_in_this_stage:
            try:
                a_tracker.add_flip(edge) 
            except ValueError:
                pass
        a_tracker.commit() 

        # Recompute edges still different from b
        current_edges_a = set(a_tracker.get_edges())
        remaining_to_flip = current_edges_a.difference(edges_b) 

        # Plot
        draw_flips(a_tracker, show_indices=False, ax=axes2_flat[plot_index]) 
        for u, v in remaining_to_flip:
            x = [points_[u].x(), points_[v].x()]
            y = [points_[u].y(), points_[v].y()]
            axes2_flat[plot_index].plot(x, y, color='red', linewidth=2)
            
        axes2_flat[plot_index].set_title(f"State After Step {real_stage_number}\n{len(remaining_to_flip)} edges differ")
        axes2_flat[plot_index].tick_params(axis='both', which='major', labelsize=8)

    # Hide unused subplots
    for i in range(total_plots, len(axes2_flat)):
        axes2_flat[i].axis('off')
        
    fig1.tight_layout()

    print("\n--- Displaying both windows ---")
    plt.show()

    print("--- All stages processed. ---")