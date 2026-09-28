from decimal import Decimal

import numpy as np

from typing import Tuple, List

from config.config_file import AMR_RADIUS
from mapf_algorithms.collision_detection.detection_object import DetectionObj


def get_action_list(paths: List[List[Tuple[str, Tuple[float, float]]]]):
    action_set = set()
    for path in paths:
        for step in path:
            _, (start, end) = step
            action_set.add(round(start*100000, 6)/100000)   # removes float arithmetic problems
            action_set.add(round((end-0.001)*100000, 6)/100000)
    action_list = list(action_set)
    action_list.sort()
    return action_list


def get_detection_objects(amr1, amr2, tau, current_action_interval, current_nodes, exgraph, speed_profiles = None):
    # create the objects with both NodeIds of the start and end node, may be the same
    amr1_obj = DetectionObj(current_nodes[amr1])

    amr2_obj = DetectionObj(current_nodes[amr2])

    ####################################################################################################################
    # determine collision interval,
    # if no speed profile is given instant acceleration and constant max speed on edge is assumed
    # get edge cost and speed for each amr
    amr1_obj.cost, amr2_obj.cost = 0, 0  # length/ cost of an edge
    amr1_obj.speed, amr2_obj.speed = 1, 1  # speed on which the edge is traversed // if speed profile later overwritten

    ####################################################################################################################
    # positions of the start and end node of the action that is executed
    ########################################################
    # starting Positions of the amrs, without passed time
    amr1_obj.ostart = np.array(
        [exgraph.nodes_obj[amr1_obj.info[0]].nodePosition.x, exgraph.nodes_obj[amr1_obj.info[0]].nodePosition.y])
    amr2_obj.ostart = np.array([exgraph.nodes_obj[amr2_obj.info[0]].nodePosition.x, exgraph.nodes_obj[
        amr2_obj.info[0]].nodePosition.y])
    ########################################################
    # ending Positions of current actions
    ########################################################
    amr1_obj.oend = np.array(
        [exgraph.nodes_obj[amr1_obj.info[1]].nodePosition.x, exgraph.nodes_obj[amr1_obj.info[1]].nodePosition.y])
    amr2_obj.oend = np.array([exgraph.nodes_obj[amr2_obj.info[1]].nodePosition.x, exgraph.nodes_obj[
        amr2_obj.info[1]].nodePosition.y])

    ####################################################################################################################
    # calculate the velocities on the edges, if on node this should be zero
    amr1_obj.new_velocity(amr1_obj.oend - amr1_obj.ostart)
    amr2_obj.new_velocity(amr2_obj.oend - amr2_obj.ostart)

    ####################################################################################################################
    # get the action intervals of the action which the amr is currently executing
    amr1_obj.action_start = current_action_interval[amr1][0]
    amr1_obj.action_end = current_action_interval[amr1][1]
    amr2_obj.action_start = current_action_interval[amr2][0]
    amr2_obj.action_end = current_action_interval[amr2][1]

    ####################################################################################################################
    # passed time since the amrs started with their actions
    passed_times = [tau - current_action_interval[amr1][0], tau - current_action_interval[amr2][0]]
    times_to_pass = [current_action_interval[amr1][1] - tau , current_action_interval[amr2][1]- tau]
    solver_start_time = min(passed_times)
    solver_end_time = min(times_to_pass)
    ####################################################################################################################
    # if the amrs change positions get the necessary edge data and calculate the current position on the edge
    ########################################################
    # AMR 1:

    # save the times in obj
    amr1_obj.passed_time = passed_times[0]
    amr1_obj.solver_start_time = solver_start_time
    amr1_obj.solver_end_time = solver_end_time
    if amr1_obj.info[0] != amr1_obj.info[1]:
        # get cost of edge (length)
        amr1_obj.cost = exgraph.graph.value(amr1_obj.info[0], amr1_obj.info[1])
        if speed_profiles is not None:
            # non-constant speed
            ########################################################
            # get the speed profile
            amr1_obj.speed_profile = speed_profiles[amr1][exgraph.get_edge_id(amr1_obj.info)]
            # calculate the speed at the time of entering the action
            amr1_obj.speed = current_speed(amr1_obj.speed_profile, solver_start_time )
            # calculate distance travelled since starting the action
            s_travelled = travelled_distance(amr1_obj.speed_profile, solver_start_time)
            # get the position
            amr1_obj.pos = amr1_obj.ostart + s_travelled * amr1_obj.velocity_norm
        else:
            # constant speed is assumed, calculate starting position accordingly
            amr1_obj.speed = exgraph.edges_obj[exgraph.get_edge_id(amr1_obj.info)].maxSpeed
            amr1_obj.pos = amr1_obj.ostart + passed_times[0] * amr1_obj.speed * amr1_obj.velocity_norm
    else:
        # the amr is on a Node
        if current_action_interval[amr1][1] == np.inf:  # the amr has finished and won't move again
            amr1_obj.speed_profile = ([{'t_start': 0.0, 't_end': np.inf, 'action': 'cruise', 'prof': 0, 's_start': 0, 's_end': 0, 'm': 0}],np.inf)
            amr1_obj.pos = amr1_obj.oend
        else:
            # calculate the speed at the time of entering the action
            if speed_profiles is not None:
                amr1_obj.speed =speed_profiles[amr1][amr1_obj.info[0]][1]
            else:
                amr1_obj.speed = 0
            # get the position
            amr1_obj.pos = amr1_obj.ostart
            pass
    ########################################################
    # AMR 2:
    amr2_obj.passed_time = passed_times[1]
    amr2_obj.solver_start_time = solver_start_time
    amr2_obj.solver_end_time = solver_end_time

    if amr2_obj.info[0] != amr2_obj.info[1]:
        amr2_obj.cost = exgraph.graph.value(amr2_obj.info[0], amr2_obj.info[1])
        if speed_profiles is not None:
            # non-constant speed
            ########################################################
            # get the speed profile
            amr2_obj.speed_profile = speed_profiles[amr2][exgraph.get_edge_id(amr2_obj.info)]
            # calculate the speed at the time of entering the action
            amr2_obj.speed = current_speed(amr2_obj.speed_profile, solver_start_time)
            # calculate distance travelled since starting the action
            s_travelled = travelled_distance(amr2_obj.speed_profile, solver_start_time)
            # get the position
            amr2_obj.pos = amr2_obj.ostart + s_travelled * amr2_obj.velocity_norm
        else:
            # constant speed is assumed, calculate starting position accordingly
            amr2_obj.speed = exgraph.edges_obj[exgraph.get_edge_id(amr2_obj.info)].maxSpeed
            amr2_obj.pos = amr2_obj.ostart + passed_times[1] * amr2_obj.speed * amr2_obj.velocity_norm
    else:
        # the amr is on a Node
        if current_action_interval[amr2][1] == np.inf:
            amr2_obj.speed_profile = ([{'t_start': 0.0, 't_end': np.inf, 'action': 'cruise', 'prof': 0, 's_start': 0, 's_end': 0, 'm': 0}],np.inf)
            amr2_obj.pos = amr2_obj.oend
        else:
            # calculate the speed at the time of entering the action
            if speed_profiles is not None:
                amr2_obj.speed = speed_profiles[amr2][amr2_obj.info[0]][1]
            else:
                amr2_obj.speed = 0
            # get the position
            amr2_obj.pos = amr2_obj.ostart
            ####################################################################################################################

    return amr1_obj, amr2_obj


def current_speed(speed_profile, passed_time):
    for phase in speed_profile[0]:
        t_start = Decimal(str(phase["t_start"]))
        t_end = Decimal(str(phase["t_end"]))
        s_start = Decimal(str(phase["s_start"]))
        prof = Decimal(str(phase["prof"]))
        dt = Decimal(str(passed_time)) - t_start

        if t_start <= passed_time <= t_end:
            if phase["action"] == "cruise":
                return float(s_start)
            else:
                return float(s_start + prof * dt)

    return float(Decimal(str(speed_profile[0][-1]["s_end"])))


def travelled_distance(speed_profile, passed_time):
    s_total = Decimal('0')
    for phase in speed_profile[0]:
        t_start = Decimal(str(phase["t_start"]))
        t_end = Decimal(str(phase["t_end"]))
        s_start = Decimal(str(phase["s_start"]))
        prof = Decimal(str(phase["prof"]))
        dt = Decimal(str(passed_time)) - t_start

        if passed_time >= t_end:
            s_total += Decimal(str(phase["m"]))
        elif t_start <= passed_time <= t_end:
            if phase["action"] == "cruise":
                s_total += s_start * dt
            else:
                s_total += s_start * dt + Decimal('0.5') * prof * dt ** 2
            break

    return float(s_total)




def create_flash_at_tau(paths, current, timestep, action_list, current_nodes, current_action_interval, exgraph, Point, Segment):
    segments = []
    tau = action_list[timestep]
    amr_radii = get_amr_radii(paths)

    for amr in range(len(paths)):
        pos, (start, end) = paths[amr][min(current[amr], len(paths[amr]) - 1)]
        # print(f"AMR {amr} at {pos} between {start, end}")
        if tau > start and tau < end - 0.001:
            # AMR stands still on node
            snode = pos
            enode = pos
            stime = start
            etime = end - 0.001
            if end - 0.001 <= action_list[min(timestep + 1, len(action_list) - 1)]:
                current[amr] += 1

        elif tau <= start:
            # AMR is driving to the node or before anything has happened
            if current[amr] <= 0:
                # AMR hasn't started existing, should not happen, assume it was at starting position
                snode = pos
                enode = pos
                stime = 0.0
                etime = end - 0.001
            else:
                enode = pos
                etime = end - 0.001
                pos2, (_, end2) = paths[amr][current[amr] - 1]
                snode = pos2
                stime = end2 - 0.001
        else:
            # AMR is driving from the node away, or last interval then infinity
            if current[amr] == len(paths[amr]) - 1:

                # if AMR has no actions left, stay on the last node, by setting the leaving time to infinity
                pos, (start, end) = paths[amr][current[amr]]
                paths[amr][current[amr]] = (pos, (start, np.inf))
                snode = pos
                enode = pos
                stime = start
                etime = np.inf
            else:
                if end == np.inf:
                    snode = pos
                    enode = pos
                    stime = start
                    etime = end
                else:
                    snode = pos
                    stime = end - 0.001
                    current[amr] += 1
                    pos2, (start2, _) = paths[amr][min(current[amr], len(paths[amr]) - 1)]
                    enode = pos2
                    etime = start2

        current_nodes[amr] = (snode, enode)  # Ids of the nodes on or between which the amr currently is
        current_action_interval[amr] = (stime, etime)  # time interval of the action that amr is doing
        # assert stime <= tau <= etime # TODO check

        start = Point(exgraph.nodes_obj[snode].nodePosition.x, exgraph.nodes_obj[snode].nodePosition.y)
        end = Point(exgraph.nodes_obj[enode].nodePosition.x, exgraph.nodes_obj[enode].nodePosition.y)
        radius = amr_radii[amr]
        if radius == 0:
            if not start.__eq__(end):
                segments.append(Segment(start, end, {amr}))
            else:
                start = Point(exgraph.nodes_obj[snode].nodePosition.x - 0.005,
                              exgraph.nodes_obj[snode].nodePosition.y - 0.5)
                end = Point(exgraph.nodes_obj[enode].nodePosition.x + 0.005, exgraph.nodes_obj[enode].nodePosition.y + 0.5)
                segments.append(Segment(start, end, {amr}))
        else:
            ############################################################################################################
            # encapsulation of amrs into whole surfaces
            # Direction vector of AMR

            vec = np.array([end.x - start.x, end.y - start.y])
            if np.linalg.norm(vec) < 1e-9:
                # AMR is stationary — just create square around the point
                vec = np.array([1, 0])
            normed_velocity = vec / np.linalg.norm(vec)
            # Two orthonormal vectors (left/right)
            v_orth1 = np.array([-normed_velocity[1], normed_velocity[0]])  # +90°
            v_orth2 = -v_orth1  # -90°

            # Offset points (start and end) in both directions scaled by radius
            start_left = np.array([start.x, start.y]) + radius * (v_orth1 - normed_velocity)
            start_right = np.array([start.x, start.y]) + radius * (v_orth2 - normed_velocity)
            end_left = np.array([end.x, end.y]) + radius * (v_orth1 + normed_velocity)
            end_right = np.array([end.x, end.y]) + radius * (v_orth2 + normed_velocity)

            # Create Point objects for the offset borders
            p_start_left = Point(start_left[0], start_left[1])
            p_start_right = Point(start_right[0], start_right[1])
            p_end_left = Point(end_left[0], end_left[1])
            p_end_right = Point(end_right[0], end_right[1])

            # Add the four boundary segments representing the swept area
            segments.append(Segment(p_start_left, p_end_left, {amr}))  # left border
            segments.append(Segment(p_start_right, p_end_right, {amr}))  # right border

            # Connect front/back arcs for completeness
            segments.append(Segment(p_start_left, p_start_right, {amr}))  # starting edge
            segments.append(Segment(p_end_left, p_end_right, {amr}))  # ending edge




    return segments, tau, current_nodes, current_action_interval, current


def get_amr_radii(paths):
    return [AMR_RADIUS for amr in paths]


def extract_behavior_change_intervals(objA, objB):
    profA, _ = objA.speed_profile
    profB, _ = objB.speed_profile

    time_points = set()
    for p in profA :
        time_points.add(objA.action_start + p['t_start'])
        time_points.add(objA.action_start + p['t_end'])
    for p in profB:
        time_points.add(objB.action_start + p['t_start'])
        time_points.add(objB.action_start + p['t_end'])

    time_points = sorted(time_points)
    #print(time_points)

    intervals = []
    for i in range(len(time_points) - 1):
        t_start = time_points[i]
        t_end = time_points[i+1]


        a_state = next((p for p in profA if objA.action_start+p['t_start'] <= t_start < objA.action_start+p['t_end']), None)
        b_state = next((p for p in profB if objB.action_start+p['t_start'] <= t_start < objB.action_start+p['t_end']), None)

        if a_state is None or b_state is None:
            continue
        intervals.append({
                't_start': t_start,
                't_end': t_end,
                'A_action': a_state['action'],
                'B_action': b_state['action'],
                'A_prof': a_state['prof'],
                'B_prof': b_state['prof'],
                'A_s_end': a_state['s_end'],
                'B_s_end': b_state['s_end']
        })

    return intervals


def get_positions_at_t(amr1_obj: DetectionObj, amr2_obj: DetectionObj, t: float):
    d1_travelled = travelled_distance(amr1_obj.speed_profile, t- amr1_obj.action_start)
    # get the position
    p1 = amr1_obj.ostart + d1_travelled * amr1_obj.velocity_norm
    #print(d1_travelled, amr1_obj.velocity_norm)
    d2_travelled = travelled_distance(amr2_obj.speed_profile, t-amr2_obj.action_start)
    # get the position
    #print(d2_travelled, amr2_obj.velocity_norm)
    p2 = amr2_obj.ostart + d2_travelled * amr2_obj.velocity_norm
    #print(p1, p2)

    return p1, p2

def get_positions_at_t_constant_speed(amr1_obj: DetectionObj, amr2_obj: DetectionObj, t: float):
    # get the position
    p1 = amr1_obj.ostart + (t- amr1_obj.action_start)* amr1_obj.speed * amr1_obj.velocity_norm
    # get the position
    p2 = amr2_obj.ostart + (t-amr2_obj.action_start) * amr2_obj.speed * amr2_obj.velocity_norm
    #print(p1, p2)

    return p1, p2



