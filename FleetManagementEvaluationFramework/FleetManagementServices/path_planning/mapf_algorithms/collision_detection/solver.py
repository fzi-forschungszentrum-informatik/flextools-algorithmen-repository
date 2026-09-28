import numpy as np

from mapf_algorithms.collision_detection.collision_detection_help_functions import extract_behavior_change_intervals, \
    current_speed, travelled_distance
from mapf_algorithms.collision_detection.detection_object import DetectionObj

from scipy.optimize import newton


def solve_for_constant_speeds(amr1: DetectionObj, amr2: DetectionObj, epsilon: float = 0.0):
    p1 = np.array(amr1.pos).reshape(-1)
    p2 = np.array(amr2.pos).reshape(-1)

    v1 = np.array(amr1.velocity_norm).reshape(-1) * amr1.speed
    v2 = np.array(amr2.velocity_norm).reshape(-1) * amr2.speed


    v_diff = v2 - v1
    p_diff = p2 - p1


    a = np.dot(v_diff, v_diff)
    b = 2 * np.dot(p_diff, v_diff)
    c = np.dot(p_diff, p_diff) - (amr1.radius + amr2.radius + epsilon) ** 2

    discriminant = b**2 - 4 * a * c

    if discriminant < 0 or a == 0:
        # No real solution
        if np.allclose(p1, p2, rtol=1e-5):
            return -np.inf, np.inf, True
        else:
            return None, None, False

    sqrt_disc = np.sqrt(discriminant)
    t1 = (-b - sqrt_disc) / (2 * a)
    t2 = (-b + sqrt_disc) / (2 * a)
    return t1, t2, False


def solve_for_varying_speeds(amrA: DetectionObj, amrB: DetectionObj, eps=0.01):
    """
    calculates the collision interval of two amrs in a fixed time interval defined by tau and
    the amrs driving behaviour as well as their profiles
    """
    ####################################################################################################################
    # get the intervals in which both AMR behaviours are unchanged,
    # if the behaviour changes -> new interval
    intervals = extract_behavior_change_intervals(amrA, amrB)
    ####################################################################################################################
    # get important data
    # get the starting positions at the solver start time
    xAo = np.array(amrA.ostart, dtype=float)
    xBo = np.array(amrB.ostart, dtype=float)

    # get the directions of the AMR
    vA_dir = np.array(amrA.velocity_norm, dtype=float)
    vB_dir = np.array(amrB.velocity_norm, dtype=float)

    # get the AMR's radii
    rA, rB = amrA.radius, amrB.radius

    # set the calculation start of the solver
    solver_start_time = amrA.solver_start_time

    ####################################################################################################################
    # empty times of collisions
    collision_times = []
    starts, ends = [], []
    for i, seg in enumerate(intervals):
        ########################################################
        # start and end times of the speed interval
        t_start, t_end = seg["t_start"], seg["t_end"]
        starts.append(t_start)
        ends.append(t_end)
        # type of actions the amrs execute in the speed interval
        actionA = seg["A_action"]
        actionB = seg["B_action"]
        # values of the actions executed on the speed interval
        profA = seg["A_prof"]
        profB = seg["B_prof"]
        ########################################################
        # skip interval which are before the solver start
        if t_end < solver_start_time :
            continue

        ########################################################
        # if the solver shall start in the executed interval set start time to solver start time
        # else use the starting time of the actions
        t_interval_start = max(t_start, solver_start_time)

        ########################################################
        # determine values for speed s and distance d at the calculations starting time
        sA0 =current_speed(amrA.speed_profile, t_start - amrA.action_start)
        sB0 = current_speed(amrB.speed_profile, t_start - amrB.action_start)
        dA0 = travelled_distance(amrA.speed_profile, t_start - amrA.action_start)
        dB0 = travelled_distance(amrB.speed_profile, t_start - amrB.action_start)
        # these are the starting points of the amrs at the starting time
        xA = xAo + vA_dir * dA0
        xB = xBo + vB_dir * dB0
        ########################################################
        # position on interval, returns the length of distance passed

        def dist_integral(t, initial_speed, profile_value, t_ref, action):
            dt = t - t_ref
            if action == "cruise":
                return profile_value * dt
            else:
                return initial_speed * dt + 0.5 * profile_value * dt**2
        ################################################################################################################
        # squared euclidean distance of the amr

        def dist2(t):
            rel = (xB + vB_dir * dist_integral(t, sB0, profB, t_interval_start, actionB)) - \
                  (xA + vA_dir * dist_integral(t, sA0, profA, t_interval_start, actionA))
            return np.dot(rel, rel)
        # distance of the
        d_target = (rA + rB + eps) ** 2
        # search for the roots on the interval and add them to the possible collisions
        try:
            t_cols = find_roots_list(dist2, d_target, t_start, t_end)
            for col in t_cols:
                collision_times.append(col)
        except Exception:
            continue

    if not collision_times:
        # there are no collisions, the heuristic was wrong
        return None, None, False

    # calculate the end times
    t0 = min(collision_times)
    t0 = max(t0, min(starts))
    t1 = max(collision_times)
    t1 = min(t1, max(ends))
    # return of the collision interval
    sp = False
    if len(collision_times) <= 2 and np.allclose(xAo, xBo, rtol=1e-5):
        sp = True
    return t0, t1, sp


def find_roots_list(dist2, d_target, t_start, t_end, tol=1e-10, max_depth=20):
    """
    Find all roots of ||xB(t)-xA(t)||^2 - d_target = 0
    in [t_start, t_end] using recursive Newton with binary interval splitting.
    Returns a list of roots (empty if none were found).
    """

    roots = []

    def recursive_search(a, b, depth=0):
        if depth > max_depth:
            return

        f = lambda t: dist2(t) - d_target
        x0 = (a + b) / 2  # start in the middle

        try:
            t_root = newton(f, x0=x0, tol=tol, maxiter=50)
        except (RuntimeError, OverflowError):
            return

        if not (a <= t_root <= b):
            return

        # check if the root is already in the list
        if not any(abs(t_root - r) < tol for r in roots):
            roots.append(t_root)

        # recurse on left and right time intervals
        if t_root - tol > a:
            recursive_search(a, t_root - tol, depth + 1)
        if t_root + tol < b:
            recursive_search(t_root + tol, b, depth + 1)

    recursive_search(t_start, t_end)
    return sorted(roots)  # sort for returning the left and rightmost roots







