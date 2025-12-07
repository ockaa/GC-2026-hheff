import networkx as nx
from itertools import combinations
from collections import defaultdict, deque
from cgshop2026_pyutils.io import read_instance
from cgshop2026_pyutils.geometry import FlippableTriangulation, draw_edges, Point 
from cgshop2026_pyutils.schemas import CGSHOP2026Instance
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
def normalize_edge(u, v):
    """Return the edge in a canonical form (smallest vertex first)."""
    return (min(u, v), max(u, v))

class DSU:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px = self.find(x)
        py = self.find(y)
        if px != py:
            self.parent[py] = px

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x


def build_flip_components(layers, a: FlippableTriangulation, max_subset_size=5):
    """
    בונה קומפוננטות flips עם תלות ביניהן.
    
    Args:
        layers: list של sets של tuples (edge, flip_partner)
        a: טרינגולציה התחלתית (FlippableTriangulation)
        max_subset_size: גודל מקסימלי של subset לבדיקה
    
    Returns:
        dsu: DSU structure with connected components
        comp_info: dict with info about each node
        Trings: list of triangulations after each layer
    """
    dsu = DSU()
    comp_info = {}
    Trings = [a]  # Trings[0] = טרינגולציה מקורית, Trings[i] = אחרי שכבה i-1
    
    all_executed_flips = []  # all_executed_flips[i] = flips בשכבה i

    # עיבוד כל שכבה
    for layer_idx, current_layer in enumerate(layers):
        print(f"\n{'='*60}")
        print(f"Processing Layer {layer_idx}")
        print(f"{'='*60}")
        
        # התחלה מהטרינגולציה אחרי השכבה הקודמת
        a_current = Trings[-1].fork()
        current_layer_flips = []
        
        # רשימת הצלעות מהשכבה הקודמת בלבד (לא מכל ההיסטוריה)
        prev_layer_edges = all_executed_flips[-1] if layer_idx > 0 else []

        for edge, e_flip in current_layer:
            edge = normalize_edge(*edge)
            e_flip = normalize_edge(*e_flip)
            node = (edge, layer_idx)
            dsu.add(node)
            
            print(f"\n--- Edge {edge} ---")
            
            # 🔴 בדיקה 1: האם זה independent flip מהטרינגולציה המקורית?
            if edge in a.possible_flips() and normalize_edge(*a.get_flip_partner(edge)) == e_flip:
                comp_info[node] = {"edge": edge, "layer": layer_idx, "enabled": set()}
                print(f"✓ Independent flip from base triangulation")
                try:
                    a_current.add_flip(edge)
                    current_layer_flips.append(edge)
                except ValueError as e:
                    print(f"✗ Failed: {e}")
                continue
            
            # 🔴 בדיקה 2: חיפוש subset מינימלי מהשכבה הקודמת
            if layer_idx == 0:
                # שכבה ראשונה - אין תלויות
                comp_info[node] = {"edge": edge, "layer": layer_idx, "enabled": set()}
                print(f"✓ Layer 0 - no dependencies")
                try:
                    a_current.add_flip(edge)
                    current_layer_flips.append(edge)
                except ValueError as e:
                    print(f"✗ Failed: {e}")
                continue
            
            # חיפוש subset מינימלי
            found_dependency_set = set()
            found = False
            
            print(f"Searching for minimal subset from prev layer ({len(prev_layer_edges)} edges)...")
            
            # 🔴 מפתח: מתחילים מהטרינגולציה לפני השכבה הקודמת!
            base_for_search = Trings[-2].fork() if layer_idx > 1 else a.fork()
            
            for size in range(1, min(len(prev_layer_edges) + 1, max_subset_size + 1)):
                if found:
                    break
                
                tested = 0
                for subset in combinations(prev_layer_edges, size):
                    tested += 1
                    a_dup = base_for_search.fork()
                    try:
                        for prev_edge in subset:
                            a_dup.add_flip(prev_edge)
                        a_dup.commit()
                        
                        if edge in a_dup.possible_flips() and normalize_edge(*a_dup.get_flip_partner(edge)) == e_flip:
                            found_dependency_set = set(subset)
                            found = True
                            print(f"✓ Found minimal subset of size {size}: {subset}")
                            break
                    except ValueError:
                        continue
                
                if tested > 0 and not found:
                    print(f"  Tested {tested} subsets of size {size} - none worked")

            # שמירת מידע
            comp_info[node] = {"edge": edge, "layer": layer_idx, "enabled": found_dependency_set}
            
            if not found:
                print(f"⚠ No enabling subset found (may need larger max_subset_size)")
            
            # יוניון עם הפליפים שנמצאו
            for dep_edge in found_dependency_set:
                dep_node = (dep_edge, layer_idx - 1)
                dsu.add(dep_node)
                dsu.union(node, dep_node)

            # הוספה לטרינגולציה
            try:
                a_current.add_flip(edge)
                current_layer_flips.append(edge)
                print(f"✓ Flip added successfully")
            except ValueError as e:
                print(f"✗ Failed to add flip: {e}")

        a_current.commit()
        Trings.append(a_current)
        all_executed_flips.append(current_layer_flips)
        
        print(f"\n✓ Layer {layer_idx} completed: {len(current_layer_flips)}/{len(current_layer)} flips succeeded")
        
        # 🔴 אזהרה אם לא הצלחנו להוסיף אף flip בשכבה
        if len(current_layer_flips) == 0:
            print(f"⚠️ WARNING: No flips succeeded in layer {layer_idx}!")
            print(f"   This layer will not appear in the dependency graph.")
            print(f"   Edges attempted: {[normalize_edge(*e[0]) for e in current_layer]}")

    return dsu, comp_info, Trings


def visualize_flip_components(comp_info, show_all=True):
    """
    מצייר DAG של קומפוננטות flips עם layout היררכי ברור.
    comp_info: dict[node] = {"edge":..., "layer":..., "enabled": set()}
    show_all: אם False, מראה רק nodes עם תלויות
    """
    G = nx.DiGraph()

    # יוצרים nodes עם תוויות
    for node, info in comp_info.items():
        edge = info["edge"]
        layer = info["layer"]
        G.add_node(node, label=f"{edge}\nL{layer}", layer=layer)

    # יוצרים edges לפי "enabled"
    edge_list = []
    for node, info in comp_info.items():
        for dep_flip in info["enabled"]:
            dep_node = None
            for n, n_info in comp_info.items():
                if n_info["edge"] == dep_flip and n_info["layer"] == info["layer"] - 1:
                    dep_node = n
                    break
            if dep_node:
                G.add_edge(dep_node, node)
                edge_list.append((dep_node, node))
    
    # אם show_all=False, מראה רק nodes שיש להם edges
    if not show_all:
        connected_nodes = set()
        for u, v in edge_list:
            connected_nodes.add(u)
            connected_nodes.add(v)
        G = G.subgraph(connected_nodes).copy()
    
    if len(G.nodes()) == 0:
        print("No dependencies found in the graph!")
        return

    # ארגון לפי שכבות
    layers_dict = {}
    for node in G.nodes():
        layer = G.nodes[node]['layer']
        if layer not in layers_dict:
            layers_dict[layer] = []
        layers_dict[layer].append(node)
    
    # מיון כל שכבה לפי שם הצלע (לעקביות)
    for layer in layers_dict:
        layers_dict[layer].sort(key=lambda n: G.nodes[n]['label'])
    
    # יצירת pos - כל שכבה בעמודה נפרדת, פיזור רחב יותר
    pos = {}
    max_layer = max(layers_dict.keys()) if layers_dict else 0
    
    for layer, nodes in sorted(layers_dict.items()):
        x = layer * 4  # ריווח גדול יותר בין שכבות
        num_nodes = len(nodes)
        
        # פיזור אנכי עם ריווח דינמי
        height_per_node = max(2.0, 20.0 / max(num_nodes, 1))
        
        for i, node in enumerate(nodes):
            y = (i - (num_nodes - 1) / 2) * height_per_node
            pos[node] = (x, y)

    # ציור
    fig_width = max(14, (max_layer + 1) * 4)
    fig_height = max(10, max(len(nodes) for nodes in layers_dict.values()) * 0.8)
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # צביעת nodes לפי שכבה
    node_colors = []
    for node in G.nodes():
        layer = G.nodes[node]['layer']
        # גרדיאנט צבעים לפי שכבה
        color_intensity = 0.3 + (layer / (max_layer + 1)) * 0.5
        node_colors.append((0.6, 0.8, 1.0, color_intensity))
    
    # nodes
    nx.draw_networkx_nodes(G, pos, node_size=1200, node_color=node_colors, 
                          edgecolors='black', linewidths=2)
    
    # edges
    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=20, 
                          width=2, edge_color="#D32F2F", alpha=0.7,
                          connectionstyle="arc3,rad=0.1")
    
    # labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')
    
    # הוספת קווים אנכיים להפרדה בין שכבות
    for layer in range(max_layer + 1):
        x = layer * 4
        plt.axvline(x=x, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
        plt.text(x, plt.ylim()[1] * 0.95, f"Layer {layer}", 
                ha='center', fontsize=12, fontweight='bold', color='#333')

    plt.title("Flip Components Dependency DAG", fontsize=18, fontweight='bold', pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
    
    # סטטיסטיקות
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes: {len(G.nodes())}")
    print(f"   Total edges: {len(G.edges())}")
    print(f"   Layers: {max_layer + 1}")
    for layer, nodes in sorted(layers_dict.items()):
        in_subgraph = [n for n in nodes if n in G.nodes()]
        print(f"   Layer {layer}: {len(in_subgraph)} nodes")
import networkx as nx
import matplotlib.pyplot as plt
import random
import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx
import matplotlib.pyplot as plt

def visualize_components(dsu, comp_info, Trings, final_edges=None, stages_of_flips_with_partner=None, show_all=True):
    """
    ציור גרף של flip-components עם הדגשת צלעות שהופכו לצלעות סופיות.

    dsu: ה-DSU שלך (עם find)
    comp_info: dict mapping node -> {"edge":..., "layer":..., "enabled": set(...) }
    Trings: רשימה של triangulations (אפשר לשמש לשכבות/pos)
    final_edges: set של צלעות סופיות (tuples), אם רוצים להדגיש
    stages_of_flips_with_partner: אופציונלי, אם רוצים להוסיף קשתות לפי זוגות מתוך המקור
    show_all: אם False, מציג רק nodes שיש להם edges
    """

    G = nx.DiGraph()

    # 1) Nodes
    all_nodes = list(comp_info.keys())
    G.add_nodes_from(all_nodes)

    # 2) Edges
    for node, info in comp_info.items():
        for dep in info.get("enabled", set()):
            dep_node = None
            target_layer = info["layer"] - 1
            for cand in comp_info.keys():
                if comp_info[cand]["edge"] == dep and comp_info[cand]["layer"] == target_layer:
                    dep_node = cand
                    break
            if dep_node:
                G.add_edge(dep_node, node)

    # קשתות משותפות
    if stages_of_flips_with_partner is not None:
        for layer_idx, flips in enumerate(stages_of_flips_with_partner):
            for edge, partner in flips:
                n1 = (tuple(sorted(edge)), layer_idx)
                n2 = (tuple(sorted(partner)), layer_idx)
                if n1 in G.nodes() and n2 in G.nodes():
                    G.add_edge(n1, n2)

    # show_all=False -> שמור רק nodes עם edges
    if not show_all:
        connected_nodes = set()
        for u, v in G.edges():
            connected_nodes.add(u); connected_nodes.add(v)
        G = G.subgraph(connected_nodes).copy()
        if len(G.nodes()) == 0:
            print("No dependencies to show after filtering (show_all=False).")
            return

    # 3) Colors per component
    reps = set(dsu.find(node) for node in comp_info.keys())
    comp_colors = {}
    palette = list(plt.cm.tab10.colors) + list(plt.cm.Pastel1.colors)
    for i, rep in enumerate(sorted(reps, key=lambda x: str(x))):
        comp_colors[rep] = palette[i % len(palette)]

    default_color = (0.85, 0.85, 0.85)
    node_colors = [comp_colors.get(dsu.find(node), default_color) for node in G.nodes()]

    # 4) Positions לפי שכבות
    layers_dict = {}
    for node in G.nodes():
        layer = comp_info[node]["layer"]
        layers_dict.setdefault(layer, []).append(node)

    for layer in layers_dict:
        layers_dict[layer].sort(key=lambda n: str(comp_info[n]["edge"]))

    max_layer = max(layers_dict.keys()) if layers_dict else 0
    pos = {}
    for layer, nodes in sorted(layers_dict.items()):
        x = layer * 4
        num_nodes = len(nodes)
        height_per_node = max(0.6, 8.0 / max(num_nodes, 1))
        for i, node in enumerate(nodes):
            y = (i - (num_nodes - 1) / 2) * height_per_node
            pos[node] = (x, y)

    # 5) ציור
    plt.figure(figsize=(max(12, (max_layer+1)*3), max(6, len(G.nodes())*0.08 + 2)))

    # Edges
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=10,
                           edge_color='#D32F2F', width=1,
                           connectionstyle="arc3,rad=0.08")

    # Nodes – נבדל בין nodes רגילים ל-final edges
    shapes = {}
    if final_edges is not None:
        final_edges_set = {tuple(sorted(e)) for e in final_edges}
    else:
        final_edges_set = set()

    for node in G.nodes():
        edge = comp_info[node]["edge"]
        if tuple(sorted(edge)) in final_edges_set:
            shapes[node] = '*'   # כוכב
        else:
            shapes[node] = 'o'   # עיגול רגיל

    unique_shapes = set(shapes.values())
    for shape in unique_shapes:
        nodes_of_shape = [n for n in G.nodes() if shapes[n] == shape]
        colors_of_nodes = [node_colors[list(G.nodes()).index(n)] for n in nodes_of_shape]
        # צבע צהוב עבור כוכבים
        if shape == '*':
            colors_of_nodes = ['gold'] * len(nodes_of_shape)
        nx.draw_networkx_nodes(G, pos,
                               nodelist=nodes_of_shape,
                               node_color=colors_of_nodes,
                               node_size=300,
                               edgecolors='black',
                               linewidths=0.8,
                               node_shape=shape)

    # Labels – compact mode
    labels = {n: f"{comp_info[n]['edge']}\nL{comp_info[n]['layer']}" for n in G.nodes()}
    if len(G.nodes()) <= 50:
        nx.draw_networkx_labels(G, pos, labels, font_size=6, font_weight='bold')

    # קווי שכבות
    for layer in range(max_layer+1):
        x = layer * 4
        plt.axvline(x=x, color='gray', linestyle='--', alpha=0.25, linewidth=0.6)
        plt.text(x, plt.ylim()[1]*0.95 if plt.ylim()[1] != 0 else 0.9, f"Layer {layer}",
                 ha='center', fontsize=10, fontweight='bold')

    plt.title("Flip Components (nodes colored by DSU component)", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    # stats
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes: {len(G.nodes())}")
    print(f"   Total edges: {len(G.edges())}")
    print(f"   Layers: {max_layer + 1}")
    for layer in sorted(layers_dict.keys()):
        print(f"   Layer {layer}: {len(layers_dict[layer])} nodes")

def optimize_flip_sequence(comp_info, original_layers):
    """
    אלגוריתם משופר עם debug מפורט:
    1. מזהה קומפוננטות בלתי תלויות
    2. לכל קומפוננטה שמתחילה בשכבה k>0: מזיז אותה k שכבות אחורה
    3. המרחק החדש = max(אורך קומפוננטה אחרי אופטימיזציה)
    """
    print("\n" + "="*60)
    print("OPTIMIZING FLIP SEQUENCE")
    print("="*60)
    
    if not comp_info:
        print("WARNING: comp_info is empty! Returning original layers.")
        flips_by_layer = [set(e for e, _ in layer) for layer in original_layers]
        return len(original_layers), flips_by_layer, original_layers
    
    # DEBUG: בדיקת תאימות
    print("\n🔍 DEBUG - Format Check:")
    if original_layers:
        sample_flip = list(original_layers[0])[0] if original_layers[0] else None
        if sample_flip:
            print(f"   Sample flip from original_layers: {sample_flip}")
            print(f"   Type: edge={type(sample_flip[0])}, partner={type(sample_flip[1])}")
    
    sample_nodes = list(comp_info.keys())[:3]
    print(f"   Sample nodes from comp_info: {sample_nodes}")
    if sample_nodes:
        print(f"   Type: {type(sample_nodes[0])}, parts: {sample_nodes[0]}")
    
    # בניית מיפוי: edge -> שכבות בהן הוא מופיע
    edge_to_layers = defaultdict(list)
    for node, info in comp_info.items():
        edge, layer = node
        edge_to_layers[edge].append(layer)
    
    print(f"\n   Total unique edges in comp_info: {len(edge_to_layers)}")
    
    # שלב 1: DSU - מציאת קומפוננטות
    dsu = DSU()
    for node in comp_info.keys():
        dsu.add(node)
    
    for node, info in comp_info.items():
        for dep_edge in info["enabled"]:
            dep_node = (dep_edge, info["layer"] - 1)
            if dep_node in comp_info:
                dsu.union(node, dep_node)
    
    components = defaultdict(list)
    for node in comp_info.keys():
        rep = dsu.find(node)
        components[rep].append(node)
    
    print(f"\nFound {len(components)} independent components")
    print(f"Total nodes in comp_info: {len(comp_info)}")
    
    # שלב 2: חישוב shift לכל קומפוננטה
    component_shift = {}
    node_to_shift = {}  # מיפוי ישיר: node -> shift
    max_component_end = 0
    
    components_with_optimization = 0
    
    for rep, nodes in components.items():
        layers = [node[1] for node in nodes]
        min_layer = min(layers)
        max_layer = max(layers)
        
        shift = min_layer
        component_length = max_layer - min_layer + 1
        
        component_shift[rep] = shift
        
        # שמור את ה-shift לכל node בקומפוננטה
        for node in nodes:
            node_to_shift[node] = shift
        
        # המרחק החדש = אורך הקומפוננטה הכי ארוכה אחרי אופטימיזציה
        optimized_length = component_length
        max_component_end = max(max_component_end, optimized_length)
        
        if shift > 0:
            components_with_optimization += 1
            print(f"✨ Component: layers {min_layer}-{max_layer}, shift={shift}, length={component_length} → optimized!")
    
    print(f"\n🎯 Components that can be optimized: {components_with_optimization}/{len(components)}")
    
    # שלב 3: בניית שכבות חדשות
    max_layers_needed = max(max_component_end, len(original_layers))
    new_layers = [set() for _ in range(max_layers_needed)]
    
    processed_optimized = 0
    processed_original = 0
    not_found = 0
    
    for original_layer_idx, layer_set in enumerate(original_layers):
        for edge, partner in layer_set:
            # נסה למצוא את ה-node המתאים
            node = (edge, original_layer_idx)
            
            if node in node_to_shift:
                # אופטימיזציה: הזז לפי הקומפוננטה
                shift = node_to_shift[node]
                new_layer_idx = original_layer_idx - shift
                processed_optimized += 1
            elif edge in edge_to_layers:
                # ה-edge קיים אבל לא בשכבה הזו - זה מוזר, נשאר במקום
                new_layer_idx = original_layer_idx
                processed_original += 1
            else:
                # ה-edge בכלל לא קיים ב-comp_info
                new_layer_idx = original_layer_idx
                not_found += 1
            
            if 0 <= new_layer_idx < max_layers_needed:
                new_layers[new_layer_idx].add((edge, partner))
    
    # שלב 4: ניקוי שכבות ריקות
    flips_with_partner = [layer for layer in new_layers if layer]
    flips_by_layer = [set(e for e, _ in layer) for layer in flips_with_partner]
    
    # סטטיסטיקות
    total_original = sum(len(layer) for layer in original_layers)
    total_optimized = sum(len(layer) for layer in flips_with_partner)
    
    print(f"\n✅ Processed (optimized): {processed_optimized} flips")
    print(f"✅ Processed (kept original): {processed_original} flips")
    print(f"⚠️  Not found in comp_info: {not_found} flips")
    print(f"✅ Total in output: {total_optimized} flips")
    
    print(f"\n{'='*60}")
    print(f"OPTIMIZATION RESULTS:")
    print(f"Original layers: {len(original_layers)}")
    print(f"Optimized layers: {len(flips_with_partner)}")
    improvement = len(original_layers) - len(flips_with_partner)
    if improvement > 0:
        print(f"✨ Improvement: {improvement} layers saved! ({improvement/len(original_layers)*100:.1f}%)")
    elif improvement < 0:
        print(f"⚠️  Slight increase: {-improvement} layers added")
    else:
        print(f"❌ No improvement - all flips stayed in original positions!")
        print(f"   Reason: processed_optimized = {processed_optimized}")
    
    print(f"Flips: {total_optimized}/{total_original}")
    if total_optimized != total_original:
        print(f"⚠️  WARNING: Lost {total_original - total_optimized} flips!")
    print(f"{'='*60}\n")
    
    return len(flips_with_partner), flips_by_layer, flips_with_partner


def optimize_and_fix_format(comp_info, original_layers):
    """Wrapper שמוודא פורמט נכון"""
    dist, flips_by_layer, flips_with_partner = optimize_flip_sequence(comp_info, original_layers)
    
    print("\n📦 Format verification:")
    print(f"   Layers: {len(flips_by_layer)}")
    if flips_by_layer:
        print(f"   Type: {type(flips_by_layer[0])}")
        print(f"   Layer 0 size: {len(flips_with_partner[0])}")
        print(f"   Example: {list(flips_with_partner[0])[:3]}")
    
    return dist, flips_by_layer, flips_with_partner