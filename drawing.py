import matplotlib.pyplot as plt
import math
from matplotlib import gridspec
from matplotlib import gridspec
from cgshop2026_pyutils.geometry import draw_edges
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_flips 
from cgshop2026_pyutils.geometry import draw_edges
def Draw_distance(dist: int,
                  stages_of_flips: list[list[tuple[int, int]]],
                  a: FlippableTriangulation,
                  b: FlippableTriangulation,
                  points_):
    """
    dist: מספר הפלפולים הכולל
    stages_of_flips: רשימת שלבי פלפולים, כל שלב = רשימת קשתות
    a, b: טריאנגולציות מסוג FlippableTriangulation
    points_: רשימת נקודות המקור (Point objects)
    """

    print(f"the distance is: {dist}")

    # --- חישוב קצוות שונים (שונה במקצת מהקוד הקודם, אבל נשאר) ---
    edges_b = set(b.get_edges())
    
    # חישוב עבור חלון 1:
    edges_a_original = set(a.get_edges())
    different_edges_a = edges_a_original.difference(edges_b)
    different_edges_b = edges_b.difference(edges_a_original)


    # --- Window 1: Original vs. Target ---
    fig1, axes1 = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

    # Plot 'a' with differing edges in red
    draw_flips(a, show_indices=True, ax=axes1[0])
    for u, v in different_edges_a:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes1[0].plot(x, y, color='red', linewidth=2)
    axes1[0].set_title(f"Triangulation 1 (Original 'a')\n{len(different_edges_a)} edges differ")

    # Plot 'b' with differing edges in red
    draw_flips(b, show_indices=True, ax=axes1[1])
    for u, v in different_edges_b:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes1[1].plot(x, y, color='red', linewidth=2)
    axes1[1].set_title(f"Triangulation 2 (Target 'b')\n{len(different_edges_b)} edges differ")


    # --- Window 2: Flip Sequence (קריאות משופרת) ---
    print("--- Creating Window 2: Flip Sequence ---")
    num_stages = len(stages_of_flips)
    total_plots = num_stages + 1
    
    # *** הגדרות גודל ופריסה משופרות ***
    ncols = 4  
    nrows = math.ceil(total_plots / ncols)
    # גודל גדול יותר, במיוחד בגובה (6 במקום 5 פר שורה), כדי לאפשר מקום ל-8 שורות
    fig2, axes2 = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, nrows * 6)) 
    axes2_flat = axes2.flat
    
    # *** שיפור קריטי 1: הוספת רווחים אנכיים ואופקיים ***
    fig2.subplots_adjust(hspace=0.4, wspace=0.3)
    
    # יצירת עותק למעקב אחר השלבים
    a_tracker = a.fork() 


    # Plot Initial State (Stage 0)
    # *** שיפור קריטי 2: הסרת אינדקסים מהרצף ***
    draw_flips(a_tracker, show_indices=False, ax=axes2_flat[0]) 
    for u, v in different_edges_a:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes2_flat[0].plot(x, y, color='red', linewidth=2)
    axes2_flat[0].set_title(f"Initial State (Stage 0)\n{len(different_edges_a)} edges differ")
    axes2_flat[0].tick_params(axis='both', which='major', labelsize=8) # הקטנת גודל טקסט הצירים

    # Loop through stages
    for i, flips_in_this_stage in enumerate(stages_of_flips):
        plot_index = i + 1

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

        # Plot the new state
        # *** שיפור קריטי 2: הסרת אינדקסים מהרצף ***
        draw_flips(a_tracker, show_indices=False, ax=axes2_flat[plot_index]) 
        for u, v in remaining_to_flip:
            x = [points_[u].x(), points_[v].x()]
            y = [points_[u].y(), points_[v].y()]
            axes2_flat[plot_index].plot(x, y, color='red', linewidth=2)
        axes2_flat[plot_index].set_title(f"State After Stage {i+1}\n{len(remaining_to_flip)} edges differ")
        axes2_flat[plot_index].tick_params(axis='both', which='major', labelsize=8) # הקטנת גודל טקסט הצירים


    # Hide unused subplots
    for i in range(total_plots, nrows * ncols):
        axes2_flat[i].axis('off')
        
    fig1.tight_layout()
    # לא נשתמש ב-tight_layout עבור fig2 כי השתמשנו ב-subplots_adjust
    # fig2.tight_layout() 

    # Show both windows
    print("\n--- Displaying both windows ---")
    plt.show()

    print("--- All stages processed. ---")


def Draw_triangulation(a: FlippableTriangulation, points_list):
    fig, ax = plt.subplots(figsize=(8, 8))

    points = points_list
    edges = a.get_edges()

    draw_edges(points, edges, ax=ax)

    for i, p in enumerate(points):
        ax.text(p.x(), p.y(), str(i), color="red", fontsize=8)

    ax.set_title("Closest Triangulation")

    plt.tight_layout()
    plt.show()

def Draw_All_Triangulation(triangulations, points_list):
    n = len(triangulations)
    cols = 2
    rows = (n + 1) // 2

    fig, axes = plt.subplots(rows, cols, figsize=(10, 5 * rows))
    axes = axes.flatten()

    for ax, tri in zip(axes, triangulations):

        points = points_list
        edges = tri.get_edges()

        draw_edges(points, edges, ax=ax)

        for i, p in enumerate(points):
            ax.text(p.x(), p.y(), str(i), color="red", fontsize=8)

        ax.set_title("Triangulation")

    plt.tight_layout()
    plt.show()



def Draw_All_Triangulation_With_Distances(triangulations, points_list, dists, closest_idx=None):
    """
    triangulations: list of FlippableTriangulation
    points_list: list of Points
    dists: n x n matrix of distances
    closest_idx: index of triangulation closest to all others
    """
    n = len(triangulations)

    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig = plt.figure(figsize=(ncols*4, nrows*3 + 2))  # מקום נוסף לטבלה

    gs = gridspec.GridSpec(nrows + 1, ncols, height_ratios=[3]*nrows + [1], hspace=0.4)

    for idx, tri in enumerate(triangulations):
        row = idx // ncols
        col = idx % ncols
        ax = fig.add_subplot(gs[row, col])

        edges = tri.get_edges()
        draw_edges(points_list, edges, ax=ax)

        for i, p in enumerate(points_list):
            ax.text(p.x(), p.y(), str(i), color='mediumvioletred', fontsize=5)

        title = f"Tri #{idx}"
        if closest_idx is not None and idx == closest_idx:
            title += " (Closest)"
            ax.set_title(title, fontweight='bold', color='deeppink')
        else:
            ax.set_title(title)
        ax.axis('off')

    ax_table = fig.add_subplot(gs[nrows, :])
    ax_table.axis('off')

    cell_text = []
    for i, row_data in enumerate(dists):
        row_sum = sum(row_data)
        row_str = [f"{d:.2f}" for d in row_data] + [f"{row_sum:.2f}"]
        cell_text.append(row_str)

    col_labels = [f"{i}" for i in range(n)] + ["Sum"]
    table = ax_table.table(cellText=cell_text,
                           rowLabels=[f"Tri #{i}" for i in range(n)],
                           colLabels=col_labels,
                           cellLoc='center',
                           rowLoc='center',
                           loc='center')

    if closest_idx is not None:
        for col in range(n + 1): 
            cell = table[closest_idx + 1, col]  
            cell.set_facecolor("pink")

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.2)

    plt.tight_layout()
    plt.show()
