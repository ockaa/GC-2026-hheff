import matplotlib.pyplot as plt
import math
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_flips, Point, draw_edges

# # --- 1. Setup Initial Triangulation ---
# points = [((0,2)), (0,0), (5,0), (5,2), (4,1), (1,1)]
# points_ = [Point(x, y) for x, y in points]
# triang_1 =[(0,5), (0,4), (1,4), (1,5), (2,4), (3,4), (4,5)]
# triang_2 = [(0,5), (1,5), (2,4), (2,5), (3,4),(3,5), (4,5)]

# a: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_, triang_1)
# b: FlippableTriangulation = FlippableTriangulation.from_points_edges(points_, triang_2)
def Draw_distance(dist: int,
                  stages_of_flips: list[list[tuple[int, int]]],
                  a: FlippableTriangulation,
                  b: FlippableTriangulation ):

    print(f"the distance is: {dist}")


    # --- 3. Window 1: Original Triangulations Side-by-Side ---
    print("--- Creating Window 1: Original vs. Target ---")
    # Create the FIRST figure and its axes
    fig1, axes1 = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

    # Plot original 'a' on the left
    draw_flips(a, show_indices=True, ax=axes1[0]) 
    axes1[0].set_title("Triangulation 1 (Original 'a')")

    # Plot 'b' on the right
    draw_flips(b, show_indices=True, ax=axes1[1])
    axes1[1].set_title("Triangulation 2 (Target 'b')")

    # --- 4. Window 2: The Flip Sequence ---
    print("--- Creating Window 2: Flip Sequence ---")
    num_stages = len(stages_of_flips)
    total_plots = num_stages + 1 # Add 1 for the initial state
    ncols = 2
    nrows = math.ceil(total_plots / ncols) 

    # Create the SECOND figure and its axes
    fig2, axes2 = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12, nrows * 6))
    axes2_flat = axes2.flat

    # Plot the Initial State (Plot 0) on the new figure
    print("Plotting Initial State (Stage 0)...")
    draw_flips(a, show_indices=True, ax=axes2_flat[0]) 
    axes2_flat[0].set_title("Initial State (Stage 0)")

    # Loop Through and Plot Each Stage on the new figure
    for i, flips_in_this_stage in enumerate(stages_of_flips):
        
        stage_number = i + 1
        plot_index = i + 1 
        
        print(f"Processing Stage {stage_number}...")
        
        # Now we modify the *original* 'a'
        for edge in flips_in_this_stage:
            try:
                a.add_flip(edge)
            except ValueError as e:
                print(f"SKIPPED flip {edge}: {e}")
                
        a.commit()
        
        # Plot the new state of 'a'
        print(f"Plotting state after Stage {stage_number}")
        draw_flips(a, show_indices=True, ax=axes2_flat[plot_index])
        axes2_flat[plot_index].set_title(f"State After Stage {stage_number}")

    # Hide any unused subplots in Window 2
    for i in range(total_plots, nrows * ncols):
        axes2_flat[i].axis('off')
    fig2.tight_layout() # Adjust layout for Window 2

    # --- 5. Show BOTH Windows at the Same Time ---
    print("\n--- Displaying both windows ---")
    plt.show() # This will open fig1 and fig2 simultaneously

    print("--- All stages processed. ---")