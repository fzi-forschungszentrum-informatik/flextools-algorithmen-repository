import json
import datetime
import logging
import os
import log_config.config

import networkx as nx

from methods.serialization import serialize_json
from data.models import NodePositionLIF, VehicleTypeNodeProperty, NodeLIF, EdgeLIF, \
    VehicleTypeEdgeProperty, LIFLayout, LIFFile, MetaInformation

logger = logging.getLogger(log_config.config.LOGGER_NAME)


def create_lif_from_network_x_graph(g: nx.graph, endpoints, layout_id='map1', max_speed=1, name_file=None,
                                    name_file_endpoints=None):

    if name_file is not None:
        os.makedirs(os.path.dirname(name_file), exist_ok=True)

    if name_file_endpoints is not None:
        os.makedirs(os.path.dirname(name_file_endpoints), exist_ok=True)

    lif_list = []
    node_list = []
    driving_nodes_list = []
    for node in g.nodes():
        x, y = node
        driving_nodes_list.append(f'N_{round(x, 2)}_{round(y, 2)}')
        node_list.append(NodeLIF(nodeId=f'N_{round(x, 2)}_{round(y, 2)}', mapId=layout_id,
                                 nodePosition=NodePositionLIF(x=x, y=y),
                                 nodeName='',
                                 vehicleTypeNodeProperties=[VehicleTypeNodeProperty(vehicleTypeId='robot',
                                                                                    theta=0,
                                                                                    actions=[])]))
    endpoints_list = []
    for node in endpoints:
        x, y = node
        endpoints_list.append(f'N_{round(x, 2)}_{round(y, 2)}')

    with open(name_file_endpoints, "w") as f:
        json.dump(endpoints_list, f)

    edge_list = []
    for u, v in g.edges():
        u_x, u_y = u
        v_x, v_y = v
        edge_list.append(EdgeLIF(edgeId=f'E-{round(u_x, 2)}_{round(u_y, 2)}-{round(v_x, 2)}_{round(v_y, 2)}',
                                 edgeName='',
                                 startNodeId=f'N_{round(u_x, 2)}_{round(u_y, 2)}', endNodeId=f'N_{round(v_x, 2)}_{round(v_y, 2)}',
                                 vehicleTypeEdgeProperties=[VehicleTypeEdgeProperty(vehicleTypeId='robot',
                                                                                    rotationAllowed=True,
                                                                                    maxSpeed=max_speed,
                                                                                    actions=[])]))
    lif_list.append(LIFLayout(layoutId=layout_id, nodes=node_list, edges=edge_list, stations=[]))
    lif_file_object = LIFFile(metaInformation=MetaInformation(projectIdentification='LIF Evaluation Test',
                                                              exportTimestamp=datetime.datetime.now(),
                                                              lifVersion='1.0.0',
                                                              creator='LIFGenerator'), layouts=lif_list)
    data_json = json.dumps(lif_file_object, indent=4, default=lambda o: serialize_json(o))
    with open(name_file, 'w') as f:
        f.write(data_json)
    logger.info(f'Lif file {name_file} finish generated with {len(node_list)} nodes and {len(edge_list)} edges!')
    return endpoints_list, driving_nodes_list
