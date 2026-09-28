import json
import random
from typing import List, Tuple

from tests.random_lif_generator.lif_generation_config import LIF_PATH, PATH_PAIRS_FILE, NUMBER_OF_PATHS


def generate_new_path_pairs_from_lif(lif_file: str, num_paths: int, output_file: str) -> Tuple[List[str], List[str]]:
    """
    Read a lif-file and generate new start and end nodes for path planning.
    :param lif_file: Path to lif-file
    :param num_paths: Number of generated paths
    :param output_file: Path to file to save results
    :return: Tuple aus Listen (start_nodes, end_nodes)
    """
    # 1. Import lif file
    with open(lif_file, "r") as f:
        lif_data = json.load(f)

    # 2. Collect nodes
    nodes = lif_data["layouts"][0]["nodes"]
    if len(nodes) < 2 * num_paths:
        raise ValueError("Nicht genug Knoten für die gewünschte Anzahl an Pfaden.")

    node_ids = [node["nodeId"] for node in nodes]
    random.shuffle(node_ids)

    # 3. Select start and goal nodes
    selected = node_ids[:2 * num_paths]
    start_nodes = selected[:num_paths]
    end_nodes = selected[num_paths:]

    # 4. Save results in json
    with open(output_file, "w") as f:
        json.dump({
            "start_nodes": start_nodes,
            "end_nodes": end_nodes
        }, f, indent=2)



    return start_nodes, end_nodes


if __name__ == "__main__":
    start_nodes, end_nodes = generate_new_path_pairs_from_lif(
        lif_file=LIF_PATH,
        num_paths=NUMBER_OF_PATHS,
        output_file=PATH_PAIRS_FILE
    )
