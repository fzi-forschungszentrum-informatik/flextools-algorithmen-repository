import logging
from typing import Dict

import numpy as np
from rtree import index

from config.config_file import LOGGER_NAME
from mapf_algorithms.collision_detection.constraints_structure.help_functions_collision_detection import obb_vs_obb, \
    point_to_oriented_bounding_box_distance
from mapf_algorithms.collision_detection.constraints_structure.zone3d import Zone3D


logger = logging.getLogger(LOGGER_NAME)


class Constraints3D:
    def __init__(self):
        p = index.Property()
        p.dimension = 3
        p.dat_extension = 'data'
        p.idx_extension = 'index'
        self.idx = index.Index(properties=p)
        self.zones: Dict[str, Zone3D] = {}   # zone_id → Zone3D

    def get_new_zone(self, start, end, radius, t_start, t_end):
        start = tuple(round(x, 4) for x in start)
        end = tuple(round(x, 4) for x in end)

        start = np.array(start, dtype=float)
        end = np.array(end, dtype=float)

        if t_end == float('inf'):
            t_end = 1e30

        velocity = end - start
        norm = np.linalg.norm(velocity)
        if norm == 0:
            # Orthogonal vectors
            start_left = start + np.array([-radius, -radius])
            start_right = start + np.array([radius, -radius])
            end_right = start + np.array([radius, radius])
            end_left = start + np.array([-radius, radius])
        else:
            # Orthogonal vectors
            normed_velocity = velocity / norm
            v_orth1 = np.array([-normed_velocity[1], normed_velocity[0]])
            v_orth2 = np.array([normed_velocity[1], -normed_velocity[0]])
            # corners
            start_left = start + radius * (v_orth1 - normed_velocity)
            start_right = start + radius * (v_orth2 - normed_velocity)
            end_left = end + radius * (v_orth1 + normed_velocity)
            end_right = end + radius * (v_orth2 + normed_velocity)

        corners = [
            tuple(start_left),
            tuple(end_left),
            tuple(end_right),
            tuple(start_right)
        ]
        return Zone3D(corners, t_start, t_end)

    def insert_zone(self, zone_id, zone):
        self.zones[zone_id] = zone
        minx, miny, maxx, maxy = zone.aabb
        box3d = (minx, miny, zone.t_start, maxx, maxy, zone.t_end)
        self.idx.insert(zone_id, box3d)

    def broad_phase_all_candidates(self, minx, miny, t_startQ, maxx, maxy, t_endQ):
        candidates = []
        for zid, zone in self.zones.items():
            z_minx, z_miny, z_maxx, z_maxy = zone.aabb
            z_t0, z_t1 = zone.t_start, zone.t_end
            if (max(minx, z_minx) <= min(maxx, z_maxx) and
                    max(miny, z_miny) <= min(maxy, z_maxy) and
                    max(t_startQ, z_t0) <= min(t_endQ, z_t1)):
                candidates.append(zid)
        return candidates

    def query_obb(self, zone: Zone3D, t_startQ, t_endQ = None):
        # query for a moving object
        # 3D Query Axis Aligned Bounding Boxes (AABB)
        if t_endQ is None:
            t_endQ = t_startQ

        corners = zone.corners
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        minx, miny = min(xs), min(ys)
        maxx, maxy = max(xs), max(ys)
        box = (minx, miny, t_startQ, maxx, maxy, t_endQ)

        # broad phase
        candidates = list(self.idx.intersection(box))

        if not candidates:
            candidates = self.broad_phase_all_candidates(minx, miny, t_startQ, maxx, maxy, t_endQ)

        logger.debug(self.zones[c] for c in self.zones.keys())
        logger.debug(zone)
        logger.debug(candidates)

        # narrow phase
        for zid in candidates:
            other_zone = self.zones[zid]

            # time overlap
            if not (other_zone.t_end >= t_startQ and other_zone.t_start <= t_endQ):
                continue

            # Narrow-phase OBB vs OBB
            if obb_vs_obb(corners, other_zone.corners):
                return True, zid
        return False, None

    def query_circle(self, center, radius, tQ):
        # query for a stationary object
        x, y = center
        minx, miny = x - radius, y - radius
        maxx, maxy = x + radius, y + radius
        box = (minx, miny, tQ, maxx, maxy, tQ)

        # broad phase
        candidates = self.idx.intersection(box)
        # narrow phase
        for zid in candidates:
            zone = self.zones[zid]
            if not (zone.t_start <= tQ <= zone.t_end):
                continue
            if point_to_oriented_bounding_box_distance(x, y, zone.corners) <= radius:
                return True, zid
        return False, None

    def next_free_time(self, query_obj, t_startQ, duration=0, is_circle=False, radius=0):
        t_candidate = t_startQ
        while True:
            # ----- Broad Phase -----
            if is_circle:
                x, y = query_obj
                minx, miny = x - radius, y - radius
                maxx, maxy = x + radius, y + radius
                box = (minx, miny, t_candidate, maxx, maxy, t_candidate + duration)
            else:
                xs = [p[0] for p in query_obj.corners]
                ys = [p[1] for p in query_obj.corners]
                minx, miny = min(xs), min(ys)
                maxx, maxy = max(xs), max(ys)
                box = (minx, miny, t_candidate, maxx, maxy, t_candidate + duration)

            candidate_ids = list(self.idx.intersection(box))

            # ----- Narrow Phase -----
            colliding_times = []
            for zid in candidate_ids:
                zone = self.zones[zid]

                if not (zone.t_start < t_candidate + duration and zone.t_end > t_candidate):
                    continue

                if is_circle:
                    x, y = query_obj
                    if point_to_oriented_bounding_box_distance(x, y, zone.corners) <= radius:
                        colliding_times.append((zone.t_start, zone.t_end))
                else:
                    if obb_vs_obb(query_obj.corners, zone.corners):
                        colliding_times.append((zone.t_start, zone.t_end))

            if not colliding_times:
                return t_candidate

            t_candidate = min(end for _, end in colliding_times)

            if t_candidate > 1e30:
                return None


    def get_constraints(self):
        constraints = list()
        for zone in self.zones.values():
            constraints.append((zone.t_start, zone.t_end, [(float(x[0]), float(x[1])) for x in zone.corners]))
        return constraints