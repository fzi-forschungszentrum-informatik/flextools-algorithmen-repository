import json
from copy import deepcopy

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from layout_graph_figures.lif_to_networkx_graph import create_networkx_graph

matplotlib.use("TkAgg")


def create_graph_density_order_figure(data, title_name, save_path, layout_image_path, layout_size, lif_file, order_file,
                                      save=False, show_figure=True):
    df = deepcopy(data)

    img = Image.open(layout_image_path)
    width_px, height_px = img.size

    length, width = layout_size

    g = create_networkx_graph(lif_file)

    order_info_dict = get_order_infos(order_file)

    for n in g.nodes:
        g.nodes[n]['order_count'] = order_info_dict.get(n, 0)

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

    node_order = [g.nodes[n].get('order_count', 0) for n in g.nodes]
    min_order, max_order = min(node_order), max(node_order)
    node_sizes = [10 + 120 * (u - min_order) / (max_order - min_order + 1e-6) for u in node_order]

    edge_usage = [g.edges[u, v].get('usage', 0) for u, v in g.edges]
    min_edge, max_edge = min(edge_usage), max(edge_usage)
    edge_widths = [2 + 8 * (u - min_edge) / (max_edge - min_edge + 1e-6) for u in edge_usage]

    cmap_edges = cm.get_cmap("RdYlGn_r")  # for usage
    cmap_nodes = cm.get_cmap("Blues")   # for pickup- and delivery locations
    norm_edges = Normalize(vmin=min_edge, vmax=max_edge)
    norm_nodes = Normalize(vmin=min_order, vmax=max_order)

    node_colors = [cmap_nodes(norm_nodes(u)) for u in node_order]
    edge_colors = [cmap_edges(norm_edges(u)) for u in edge_usage]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.imshow(img)

    pos = {}
    for n in g.nodes:
        x_m = g.nodes[n]['x']
        y_m = g.nodes[n]['y']
        x_px = (x_m / length) * width_px
        y_px = (y_m / width) * height_px
        pos[n] = (x_px, y_px)

    nodes_with_orders = [n for n in g.nodes if g.nodes[n].get('order_count', 0) > 0]
    nodes_without_orders = [n for n in g.nodes if g.nodes[n].get('order_count', 0) == 0]

    node_size_dict = {n: size for n, size in zip(g.nodes, node_sizes)}
    node_color_dict = {n: color for n, color in zip(g.nodes, node_colors)}

    nx.draw_networkx_nodes(
        g,
        pos=pos,
        nodelist=nodes_without_orders,
        node_size=[node_size_dict[n] for n in nodes_without_orders],
        node_color=[node_color_dict[n] for n in nodes_without_orders],
        node_shape='o',
        edgecolors='black',
        linewidths=0.3,
        ax=ax
    )


    nx.draw_networkx_nodes(
        g,
        pos=pos,
        nodelist=nodes_with_orders,
        node_size=[node_size_dict[n] for n in nodes_with_orders],
        node_color=[node_color_dict[n] for n in nodes_with_orders],
        node_shape='^',
        edgecolors='black',
        linewidths=0.3,
        ax=ax
    )

    nx.draw_networkx_edges(g, pos=pos, edgelist=g.edges, width=edge_widths, edge_color=edge_colors, ax=ax)

    sm_edges = ScalarMappable(cmap=cmap_edges, norm=norm_edges)
    sm_edges.set_array([])
    cbar_edges = fig.colorbar(sm_edges, ax=ax, fraction=0.022, pad=0.04)
    cbar_edges.set_label("Abs. number of passages edges", rotation=270, labelpad=15, fontsize=14)

    sm_nodes = ScalarMappable(cmap=cmap_nodes, norm=norm_nodes)
    sm_nodes.set_array([])
    cbar_nodes = fig.colorbar(sm_nodes, ax=ax, fraction=0.022, pad=0.06)
    cbar_nodes.set_label("Number of pickup and delivery location nodes", rotation=270, labelpad=15, fontsize=14)


    plt.title(title_name, fontsize=18, fontweight='bold')
    plt.axis("off")
    plt.tight_layout()
    if save:
        plt.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return


def get_order_infos(order_file):
    order_info_dict = {}

    f = open(order_file, "r")
    data = json.load(f)
    f.close()

    for i, order in enumerate(data):
        if order['sourceId'] in order_info_dict.keys():
            order_info_dict[order['sourceId']] += 1
        else:
            order_info_dict[order['sourceId']] = 1
        if order['sinkId'] in order_info_dict.keys():
            order_info_dict[order['sinkId']] += 1
        else:
            order_info_dict[order['sinkId']] = 1
    return order_info_dict

