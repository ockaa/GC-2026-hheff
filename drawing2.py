import matplotlib.pyplot as plt
import math
# נניח שהשארת את ה-imports האלו
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_flips 

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

    # --- Compute edges that differ between a and b ---
    # נשאר ללא שינוי, זה רק חישוב ראשוני
    edges_a = set(a.get_edges())
    edges_b = set(b.get_edges())
    different_edges_a = edges_a.difference(edges_b)
    different_edges_b = edges_b.difference(edges_a)

    # --- Window 1: Original vs. Target ---
    print("--- Creating Window 1: Original vs. Target ---")
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
    
    # *** שיפור קריאות: שינוי פריסה וגודל ***
    ncols = 4  # נגדיל ל-4 עמודות
    nrows = math.ceil(total_plots / ncols)
    # נגדיל את ה-figsize לרוחב 20 וגובה 5 פר שורה
    fig2, axes2 = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, nrows * 5))
    axes2_flat = axes2.flat
    
    # כדי שנוכל לבצע היפוכים מבלי לשנות את 'a' המקורי (שמשורטט בחלון 1),
    # אנו חייבים ליצור עותק חדש עבור מעקב אחר השלבים.
    # *** שינוי קריטי: יצירת עותק של a עבור מעקב השלבים ***
    a_tracker = a.fork() 


    # Plot Initial State (Stage 0)
    # *** שיפור קריאות: הסרת show_indices=True ***
    draw_flips(a_tracker, show_indices=False, ax=axes2_flat[0]) 
    for u, v in different_edges_a:
        x = [points_[u].x(), points_[v].x()]
        y = [points_[u].y(), points_[v].y()]
        axes2_flat[0].plot(x, y, color='red', linewidth=2)
    axes2_flat[0].set_title(f"Initial State (Stage 0)\n{len(different_edges_a)} edges differ")

    # Loop through stages
    for i, flips_in_this_stage in enumerate(stages_of_flips):
        plot_index = i + 1

        # Apply flips
        for edge in flips_in_this_stage:
            try:
                # עובדים על העותק
                a_tracker.add_flip(edge) 
            except ValueError:
                pass
        a_tracker.commit() # עובדים על העותק

        # Recompute edges still different from b
        current_edges_a = set(a_tracker.get_edges())
        # משתמשים ב-edges_b המקוריות שחושבו בהתחלה
        remaining_to_flip = current_edges_a.difference(edges_b) 

        # Plot the new state
        # *** שיפור קריאות: הסרת show_indices=True ***
        draw_flips(a_tracker, show_indices=False, ax=axes2_flat[plot_index]) 
        for u, v in remaining_to_flip:
            x = [points_[u].x(), points_[v].x()]
            y = [points_[u].y(), points_[v].y()]
            axes2_flat[plot_index].plot(x, y, color='red', linewidth=2)
        axes2_flat[plot_index].set_title(f"State After Stage {i+1}\n{len(remaining_to_flip)} edges differ")

    # Hide unused subplots
    for i in range(total_plots, nrows * ncols):
        axes2_flat[i].axis('off')
        
    fig1.tight_layout() # סידור החלון הראשון
    fig2.tight_layout() # סידור החלון השני

    # Show both windows
    print("\n--- Displaying both windows ---")
    plt.show()

    print("--- All stages processed. ---")