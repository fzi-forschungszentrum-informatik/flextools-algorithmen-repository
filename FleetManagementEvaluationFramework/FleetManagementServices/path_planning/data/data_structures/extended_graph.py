import json
from typing import List, Type

import config.config_file
from data.models import Node, Edge, Station
from data.data_structures.graph import Graph


class ExtendedGraph:

    def __init__(self, nodes_and_stations, init_graph,  nodes_lif: List[Node] = None, edges_lif: List[Edge] = None,
                 stations_lif: List[Station] = None):
        self.graph = Graph(nodes_and_stations, init_graph, config.config_file.DIRECTED_GRAPH)
        self.nodes = []
        self.edges = []

        self.nodes_to_edge = {}
        self.nodes_obj = {}
        self.edges_obj = {}
        self.stations_obj = {}
        for node in nodes_lif:
            self.nodes.append(node.nodeId)
            self.nodes_obj[node.nodeId] = node

        for edge in edges_lif:
            self.nodes_to_edge[frozenset([edge.startNodeId, edge.endNodeId])] = edge.edgeId
            self.edges.append(edge.edgeId)
            self.edges_obj[edge.edgeId] = edge

        for station in stations_lif:
            self.nodes.append(station.stationId)
            self.stations_obj[station.stationId] = station

    def get_edge_id(self, nodes: List[str]):
        return self.nodes_to_edge.get(frozenset(nodes))

    def serialize_graph(self):
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "nodes_to_edge": {
                ",".join(sorted(edge_set)): edge_id
                for edge_set, edge_id in self.nodes_to_edge.items()
            },
            "nodes_obj": {k: v.model_dump() for k, v in self.nodes_obj.items()},
            "edges_obj": {k: v.model_dump() for k, v in self.edges_obj.items()},
            "stations_obj": {k: v.model_dump() for k, v in self.stations_obj.items()},
        }

    @classmethod
    def from_json(cls, json_path: str, node_class: Type[Node], edge_class: Type[Edge], station_class: Type[Station]):
        with open(json_path, "r") as f:
            data = json.load(f)

        # Reconstruct model objects
        nodes_obj = {
            node_id: node_class(**attrs)
            for node_id, attrs in data["nodes_obj"].items()
        }
        edges_obj = {
            edge_id: edge_class(**attrs)
            for edge_id, attrs in data["edges_obj"].items()
        }
        stations_obj = {
            station_id: station_class(**attrs)
            for station_id, attrs in data["stations_obj"].items()
        }

        nodes_lif = list(nodes_obj.values())
        edges_lif = list(edges_obj.values())
        stations_lif = list(stations_obj.values())

        # Recreate init_graph and nodes_and_stations from edges
        init_graph = {}
        nodes_and_stations = []

        for edge in edges_lif:
            # Add start node
            if edge.startNodeId not in nodes_and_stations:
                nodes_and_stations.append(edge.startNodeId)
                init_graph[edge.startNodeId] = {}
            # Add end node
            if edge.endNodeId not in nodes_and_stations:
                nodes_and_stations.append(edge.endNodeId)
                init_graph[edge.endNodeId] = {}

            # Fill connection (assumes undirected, could be changed)
            travel_time = round(edge.length / edge.maxSpeed, 2)
            init_graph[edge.startNodeId][edge.endNodeId] = travel_time
            init_graph[edge.endNodeId][edge.startNodeId] = travel_time

        # Add stations (if not already added)
        for station in stations_lif:
            if station.stationId not in nodes_and_stations:
                nodes_and_stations.append(station.stationId)
                init_graph[station.stationId] = {}

        return cls(
            nodes_lif=nodes_lif,
            edges_lif=edges_lif,
            stations_lif=stations_lif,
            nodes_and_stations=nodes_and_stations,
            init_graph=init_graph
        )