from copy import deepcopy

import matplotlib

from layout_graph_figures.lif_to_networkx_graph import create_networkx_graph

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable


def create_graph_density_figure(data, title_name, save_path, layout_image_path, layout_size, lif_file,
                                save=False, show_figure=True):
    df = deepcopy(data)

    img = Image.open(layout_image_path)
    width_px, height_px = img.size

    length, width = layout_size

    g = create_networkx_graph(lif_file)

    for _, row in df.iterrows():
        key = row['Key']
        value = row['Value']
        if key.startswith("N_") and key in g.nodes:
            g.nodes[key]['usage'] = value
        elif key.startswith("E-"):
            for u, v, d in g.edges(data=True):
                if d.get('edgeId') == key:
                    g.edges[u, v]['usage'] = value
                    break

    node_usage = [g.nodes[n].get('usage', 0) for n in g.nodes]
    min_node, max_node = min(node_usage), max(node_usage)
    node_sizes = [5 + 65 * (u - min_node) / (max_node - min_node + 1e-6) for u in node_usage]

    edge_usage = [g.edges[u, v].get('usage', 0) for u, v in g.edges]
    min_edge, max_edge = min(edge_usage), max(edge_usage)
    edge_widths = [1 + 6 * (u - min_edge) / (max_edge - min_edge + 1e-6) for u in edge_usage]

    all_usage = node_usage + edge_usage
    min_usage = min(all_usage)
    max_usage = max(all_usage)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(img)

    cmap = cm.get_cmap("RdYlGn_r")
    norm = Normalize(vmin=min_usage, vmax=max_usage)
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    node_colors = [cmap(norm(u)) for u in node_usage]
    edge_colors = [cmap(norm(u)) for u in edge_usage]

    pos = {}
    for n in g.nodes:
        x_m = g.nodes[n]['x']
        y_m = g.nodes[n]['y']
        x_px = (x_m / length) * width_px
        y_px = height_px - (y_m / width) * height_px
        pos[n] = (x_px, y_px)

    nx.draw_networkx_nodes(g, pos=pos, nodelist=g.nodes, node_size=node_sizes, node_color=node_colors, ax=ax)
    nx.draw_networkx_edges(g, pos=pos, edgelist=g.edges, width=edge_widths, edge_color=edge_colors, ax=ax)

    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.0)
    cbar.set_label("Abs. number of passages nodes and edges", rotation=270, labelpad=15, fontsize=14)

    plt.title(title_name, fontsize=18, fontweight='bold')
    plt.axis("off")
    plt.tight_layout()
    if save:
        plt.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return

