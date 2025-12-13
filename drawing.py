import matplotlib.pyplot as plt
import math
from tqdm import tqdm
from cgshop2026_pyutils.geometry import draw_edges, FlippableTriangulation, draw_flips
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import gridspec
import networkx as nx
from c_builder import ConnectedDirectedComponent, DynamicGraphManager

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


def Draw_Manager_Components(manager):
    """
    Visualizes the connected components stored in the DynamicGraphManager.
    """
    
    # 1. Get all components
    components = manager.get_all_components()
    n_components = len(components)
    
    if n_components == 0:
        print("Manager is empty. Nothing to plot.")
        return

    print(f"--- Visualizing {n_components} Connected Components ---")

    # 2. Setup Grid Layout
    # Fixed 3 columns
    ncols = 3
    nrows = math.ceil(n_components / ncols)
    
    # Create subplots
    # squeeze=False ensures 'axes' is ALWAYS a 2D array [[ax, ax], [ax, ax]]
    # This prevents the confusing behavior where it sometimes returns a single object.
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 5 * nrows), squeeze=False)
    
    # Flatten into a simple 1D list [ax1, ax2, ax3, ...]
    axes_flat = axes.flatten()

    # 3. Iterate and Draw
    for i, comp in enumerate(components):
        ax = axes_flat[i]  # Now guaranteed to be a single Axes object
        
        # Create NetworkX Directed Graph
        G = nx.DiGraph()
        
        # Add Nodes & Edges from the component
        for u, neighbors in comp.graph.items():
            for v in neighbors:
                G.add_edge(u, v)
        
        # Also add isolated nodes
        for node in comp.nodes:
            if node not in G:
                G.add_node(node)

        # Identify Heads for coloring
        heads = comp.get_heads()
        
        # Color map
        node_colors = []
        for node in G.nodes():
            if node in heads:
                node_colors.append('lightgreen')
            else:
                node_colors.append('skyblue')

        # Layout Algorithm
        try:
            pos = nx.spring_layout(G, k=0.5, iterations=50)
        except:
            pos = nx.random_layout(G)

        # Draw
        nx.draw(G, pos, ax=ax, 
                with_labels=True, 
                node_color=node_colors, 
                edge_color='gray', 
                node_size=500, 
                font_size=8, 
                font_weight='bold',
                arrows=True, 
                arrowstyle='-|>', 
                arrowsize=12)
        
        ax.set_title(f"Component #{i+1}\nNodes: {len(G.nodes)} | Heads: {len(heads)}")
        ax.axis('off')

    # 4. Hide unused subplots
    for j in range(n_components, len(axes_flat)):
        axes_flat[j].axis('off')

    plt.tight_layout()
    plt.show()

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
def Draw_All_Triangulation_With_Distances(triangulations, points_list, dists_result, closest_idx=None, imposter=False):
    n = len(triangulations)

    # מטריצה של מרחקים בלבד
    dists = [[t[0] for t in row] for row in dists_result]

    # במקרה שיש impostor – מוציאים את העמודה האחרונה מהטבלה
    if imposter:
        # Remove last column FROM EACH ROW — but keep rows
        dists_for_table = [row[:-1] for row in dists]
        effective_n = n - 1
    else:
        dists_for_table = dists
        effective_n = n

    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig = plt.figure(figsize=(ncols*4, nrows*3 + 2))
    gs = plt.GridSpec(nrows + 1, ncols, height_ratios=[3]*nrows + [1], hspace=0.4)

    # ציור טריאנגולציות
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

    # טבלה
    ax_table = fig.add_subplot(gs[nrows, :])
    ax_table.axis('off')

    cell_text = []
    for i, row_data in enumerate(dists_for_table):
        row_sum = sum(row_data)  # סכום לא כולל העמודה האחרונה
        row_str = [f"{d:.2f}" for d in row_data] + [f"{row_sum:.2f}"]
        cell_text.append(row_str)

    # כותרות עמודות
    col_labels = [f"{i}" for i in range(effective_n)] + ["Sum"]

    table = ax_table.table(
        cellText=cell_text,
        rowLabels=[f"Tri #{i}" for i in range(n)],
        colLabels=col_labels,
        cellLoc='center',
        rowLoc='center',
        loc='center'
    )

    # צביעת השורה של ה־closest
    if closest_idx is not None:
        # השורה בטבלה היא closest_idx + 1 (כי יש שורת כותרות)
        # אבל צריך לצבוע את כל העמודות (כולל Sum)
        for col in range(effective_n + 2):  # +2 כי יש גם עמודת row labels וגם Sum
            try:
                cell = table[closest_idx + 1, col]
                cell.set_facecolor("pink")
                cell.set_text_props(weight='bold')
            except:
                pass  # במקרה של עמודת row labels

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.2)

    plt.tight_layout()
    plt.show()
 
def Save_All_To_PDF(
        triangulations,
        points_list,
        dists_result,
        closest_idx=None,
        filename="triangulations_report7.pdf",
        imposter=False
    ):
    
    n = len(triangulations)
    effective_n = n - 1 if imposter else n

    with PdfPages(filename) as pdf:

        # ======================
        # דפי רצף הפליפים
        # ======================
        total_pairs = n * (n - 1) // 2
        print(f"[Info] Generating flip sequences for {total_pairs} pairs...")

        pair_count = 0
        for i in range(n):
            for j in range(i + 1, n):
                dist, stages_of_flips, _ = dists_result[i][j]

                print(f"[Info] Building PDF page for pair {i}-{j} (distance={dist})")

                fig = plt.figure(figsize=(20, 6))
                Draw_distance_for_pdf(
                    dist, stages_of_flips,
                    triangulations[i], triangulations[j],
                    points_list, fig=fig,
                    pair_title=f"Pair {i}-{j}"
                )

                pdf.savefig(fig)
                plt.close(fig)

                pair_count += 1
                print(f"[Info] Finished pair {i}-{j}")

        # ======================
        # עמוד 1: כל הטריאנגולציות
        # ======================
        print("[Info] Creating triangulations overview page...")

        ncols = 3
        nrows = (n + ncols - 1) // ncols
        fig1 = plt.figure(figsize=(ncols * 4, nrows * 3.5))

        for idx, tri in enumerate(triangulations):
            ax = fig1.add_subplot(nrows, ncols, idx + 1)
            draw_edges(points_list, tri.get_edges(), ax=ax)

            for p_idx, p in enumerate(points_list):
                ax.text(p.x(), p.y(), str(p_idx), color='mediumvioletred', fontsize=5)

            title = f"Tri #{idx}"
            if closest_idx is not None and idx == closest_idx:
                title += " (Closest)"
                ax.set_title(title, fontweight='bold', color='deeppink')
            else:
                ax.set_title(title)

            ax.axis('off')

        fig1.suptitle("All Triangulations", fontsize=16, color='deeppink', y=0.98)
        fig1.tight_layout()
        pdf.savefig(fig1)
        plt.close(fig1)

        # ======================
        # עמוד 2: טבלת מרחקים
        # ======================
        print("[Info] Creating distance matrix page...")

        fig2 = plt.figure(figsize=(12, 8))
        ax_table = fig2.add_subplot(111)
        ax_table.axis('off')

        cell_text = []

        for i, row_data in enumerate(dists_result):
            # מרחקים בלבד
            row = [d[0] for d in row_data]

            # במקרה של impostor — מורידים העמודה האחרונה
            if imposter:
                row = row[:-1]

            row_sum = sum(row)
            row_str = [f"{v:.0f}" for v in row] + [f"{row_sum:.0f}"]

            cell_text.append(row_str)

        col_labels = [f"Tri #{i}" for i in range(effective_n)] + ["Sum"]

        table = ax_table.table(
            cellText=cell_text,
            rowLabels=[f"Tri #{i}" for i in range(n)],
            colLabels=col_labels,
            cellLoc='center',
            rowLoc='center',
            loc='center'
        )

        # צביעת הכי קרובה
        if closest_idx is not None:
            for col in range(effective_n + 1):  # כולל SUM
                cell = table[closest_idx + 1, col]
                cell.set_facecolor("pink")
                cell.set_text_props(weight='bold')

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        fig2.suptitle("Distance Matrix", fontsize=16, color='deeppink', y=0.95)
        pdf.savefig(fig2)
        plt.close(fig2)

        print(f"[Done] PDF saved as '{filename}'")



def Draw_distance_for_pdf(dist, stages_of_flips, a, b, points_, fig=None, pair_title="Pair"):
    """
    dist: מספר הפליפים הכולל
    stages_of_flips: רשימת שלבי פליפים, כל שלב = רשימת קשתות
    a, b: טריאנגולציות מסוג FlippableTriangulation
    points_: רשימת נקודות המקור (Point objects)
    fig: פיגורה קיימת (אם רוצים להשתמש בקיימת)
    pair_title: כותרת עליונה לזוג
    """
    
    print(f"\n=== Processing {pair_title} ===")
    print(f"the distance is: {dist}")

    # --- חישוב קצוות שונים ---
    edges_b = set(b.get_edges())
    
    # חישוב עבור חלון 1:
    edges_a_original = set(a.get_edges())
    different_edges_a = edges_a_original.difference(edges_b)

    # --- Flip Sequence (בדיוק כמו בפונקציה המקורית) ---
    print("--- Creating Flip Sequence for PDF ---")
    num_stages = len(stages_of_flips)
    total_plots = num_stages + 1
    
    # הגדרות גודל ופריסה
    ncols = 4  
    nrows = math.ceil(total_plots / ncols)
    
    # יצירת הפיגורה
    if fig is None:
        fig = plt.figure(figsize=(20, nrows * 6))
    
    # יצירת subplots
    axes2 = fig.subplots(nrows=nrows, ncols=ncols)
    if nrows == 1 and ncols == 1:
        axes2_flat = [axes2]
    elif nrows == 1 or ncols == 1:
        axes2_flat = axes2.flatten()
    else:
        axes2_flat = axes2.flat
    
    # הוספת רווחים אנכיים ואופקיים
    fig.subplots_adjust(hspace=0.4, wspace=0.3)
    
    # כותרת עליונה ורודה
    fig.suptitle(f"{pair_title} Flip Sequence (Distance: {dist})", fontsize=16, color='deeppink')
    
    # יצירת עותק למעקב אחר השלבים
    a_tracker = a.fork() 

    # Plot Initial State (Stage 0)
    draw_flips(a_tracker, show_indices=False, ax=axes2_flat[0]) 
    for u, v in different_edges_a:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes2_flat[0].plot(x, y, color='hotpink', linewidth=2)
    axes2_flat[0].set_title(f"Initial State (Stage 0)\n{len(different_edges_a)} edges differ")
    axes2_flat[0].tick_params(axis='both', which='major', labelsize=8)

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
        draw_flips(a_tracker, show_indices=False, ax=axes2_flat[plot_index]) 
        for u, v in remaining_to_flip:
            x = [points_[u].x(), points_[v].x()]
            y = [points_[u].y(), points_[v].y()]
            axes2_flat[plot_index].plot(x, y, color='hotpink', linewidth=2)
        axes2_flat[plot_index].set_title(f"State After Stage {i+1}\n{len(remaining_to_flip)} edges differ")
        axes2_flat[plot_index].tick_params(axis='both', which='major', labelsize=8)

    # Hide unused subplots
    for i in range(total_plots, nrows * ncols):
        axes2_flat[i].axis('off')

    print("--- Flip sequence created for PDF ---")
    
    # החזרת הפיגורה (לא מציגים אותה, רק מחזירים)
    return fig