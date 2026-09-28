import re
import ast
import numpy as np
import matplotlib.pyplot as plt


def extract_detection_blocks(text_inp):
    blocks = []
    i = 0
    n = len(text_inp)
    while i < n:
        idx = text_inp.find("detectionObj(", i)
        if idx == -1:
            break
        start = idx + len("detectionObj(")
        depth = 1
        j = start
        while j < n and depth > 0:
            if text_inp[j] == "(":
                depth += 1
            elif text_inp[j] == ")":
                depth -= 1
            j += 1
        blocks.append(text_inp[start:j - 1])
        i = j
    return blocks


def parse_detection_objects(text_inp):
    """DetectionObj-Block to dict."""
    objs = []
    blocks = extract_detection_blocks(text_inp)

    for block in blocks:
        data = {}
        arr_fields = ['pos', 'velocity', 'velocity_norm', 'ostart', 'oend']
        for field in arr_fields:
            m = re.search(fr"{field}=\[(.*?)\]", block, re.DOTALL)
            if m:
                nums = [float(x) for x in m.group(1).split()]
                data[field] = np.array(nums)

        # info
        m = re.search(r"info=\((.*?)\)", block)
        if m:
            data['info'] = tuple(s.strip().strip("'") for s in m.group(1).split(','))

        # floats
        float_fields = ['speed', 'cost', 'radius', 'passed_time', 'action start', 'action end']
        for field in float_fields:
            m = re.search(fr"{field}=([0-9\.\-e]+)", block)
            if m:
                data[field] = float(m.group(1))

        # speed_profile
        m = re.search(r"speed_profile=\((\[.*?\]),\s*([0-9\.\-e]+)\)", block, re.DOTALL)
        if m:
            data['speed_profile'] = (eval(m.group(1)), float(m.group(2)))

        if 'pos' in data:
            objs.append(data)
    return objs



def simulate_motion(obj):
    """
    Compute exact position for each segment
    """
    action_start = obj.get('action start', 0)
    action_end = obj.get('action end', 0)
    pos = np.array(obj['ostart'], dtype=float)
    vnorm = np.array(obj['velocity_norm'], dtype=float)
    profiles, _ = obj['speed_profile']

    # results
    t_list = [action_start]
    x_list = [pos[0]]
    y_list = [pos[1]]

    t_local = 0.0
    for seg in profiles:
        dt = seg['t_end'] - seg['t_start']
        m_seg = seg['m']
        # Compute new position
        pos = pos + m_seg * vnorm

        t_local += dt
        t_list.append(action_start + t_local)
        x_list.append(pos[0])
        y_list.append(pos[1])

    if action_end > action_start + t_local:
        t_list.append(action_end)
        x_list.append(pos[0])
        y_list.append(pos[1])

    return np.array(t_list), np.array(x_list), np.array(y_list)

def plot_objects(text_inp):
    objs = parse_detection_objects(text_inp)
    plt.figure(figsize=(8,5))
    for obj in objs:
        t, x, y = simulate_motion(obj)
        plt.plot(t, x, label=f"{obj['info'][0]}→{obj['info'][1]} (x)")
        plt.plot(t, y, '--', label=f"{obj['info'][0]}→{obj['info'][1]} (y)")
    plt.xlabel("Zeit [s]")
    plt.ylabel("Position")
    plt.legend()
    plt.grid(True)
    plt.title("Positionsverlauf der detectionObj")
    plt.show()


def plot_objects_with_distances(text):
    objs = parse_detection_objects(text)
    simulations = []

    # Zuerst simulieren wir alle Objekte
    for obj in objs:
        t, x, y = simulate_motion(obj)
        simulations.append({'info': obj['info'], 't': t, 'x': x, 'y': y})

    plt.figure(figsize=(12,5))

    # --- Position-Time-Curve ---
    plt.subplot(1, 2, 1)
    for sim in simulations:
        plt.plot(sim['t'], sim['x'], label=f"{sim['info'][0]}→{sim['info'][1]} (x)")
        plt.plot(sim['t'], sim['y'], '--', label=f"{sim['info'][0]}→{sim['info'][1]} (y)")
    plt.xlabel("Time [s]")
    plt.ylabel("Position")
    plt.title("Position-Time-Curve")
    plt.legend()
    plt.grid(True)

    # --- Distance between all paths ---
    plt.subplot(1, 2, 2)
    n = len(simulations)
    for i in range(n):
        for j in range(i+1, n):
            # Interpolation
            t_common = np.linspace(
                max(simulations[i]['t'][0], simulations[j]['t'][0]),
                min(simulations[i]['t'][-1], simulations[j]['t'][-1]),
                100
            )
            x_i = np.interp(t_common, simulations[i]['t'], simulations[i]['x'])
            x_j = np.interp(t_common, simulations[j]['t'], simulations[j]['x'])
            y_i = np.interp(t_common, simulations[i]['t'], simulations[i]['y'])
            y_j = np.interp(t_common, simulations[j]['t'], simulations[j]['y'])
            rA, rB, eps = 0.1, 0.1, 0.1
            dx =( x_i - x_j)**2  -(rA + rB + eps) ** 2
            dy = (y_i - y_j)**2  -(rA + rB + eps) ** 2

            plt.plot(t_common, dx, label=f"{simulations[i]['info'][0]}-{simulations[j]['info'][0]} dx")
            plt.plot(t_common, dy, '--', label=f"{simulations[i]['info'][0]}-{simulations[j]['info'][0]} dy")

    plt.xlabel("Time [s]")
    plt.ylabel("Distance")
    plt.title("Distance between two objects (x und y)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    text = """
detectionObj(
  info=('N_22_23', 'N_19_23'),
  ostart=[22. 23.],
  oend=[19. 23.],
  pos=[21.872 23.   ],
  velocity=[-3.  0.],
  velocity_norm=[-1.  0.],
  speed=0.68,
  cost=3.0,
  radius=0.2,
  speed_profile=([{'t_start': 0.0, 't_end': 1.0, 'action': 'accelerate', 'prof': 0.4, 's_start': 0.6, 's_end': 1.0, 'm': 0.8}, {'t_start': 1.0, 't_end': 2.4, 'action': 'cruise', 'prof': 1, 's_start': 1, 's_end': 1, 'm': 1.4}, {'t_start': 2.4, 't_end': 3.4, 'action': 'decelerate', 'prof': -0.4, 's_start': 1, 's_end': 0.6, 'm': 0.8}], 3.4000000000000004),
  passed_time=1.5902277713535566
,  action start=3.1097722286464435
,  action end=6.509772228646444
)
******************
detectionObj(
  info=('N_18_23', 'N_19_23'),
  ostart=[18. 23.],
  oend=[19. 23.],
  pos=[18.2 23. ],
  velocity=[1. 0.],
  velocity_norm=[1. 0.],
  speed=0.9999999999999999,
  cost=1.0,
  radius=0.2,
  speed_profile=([{'t_start': 0.0, 't_end': 0.2, 'action': 'cruise', 'prof': 1, 's_start': 1, 's_end': 1, 'm': 0.2}, {'t_start': 0.2, 't_end': 1.2, 'action': 'decelerate', 'prof': -0.4, 's_start': 1, 's_end': 0.6, 'm': 0.8}], 1.2000000000000002),
  passed_time=0.20000000000000018
,  action start=4.5
,  action end=5.7
)
"""
    t2 = """
detectionObj(
  info=('N_4_15', 'N_4_15'),
  ostart=[ 4. 15.],
  oend=[ 4. 15.],
  pos=None,
  velocity=[0. 0.],
  velocity_norm=[0. 0.],
  speed=1,
  cost=0,
  radius=0.0,
  speed_profile=([{'t_start': 0.0, 't_end': inf, 'action': 'cruise', 'prof': 0, 's_start': 0, 's_end': 0, 'm': 0}], inf),
  passed_time=1.8500000000000014
,  action start=14.2
,  action end=inf
)
******************
detectionObj(
  info=('N_12_15', 'N_4_15'),
  ostart=[12. 15.],
  oend=[ 4. 15.],
  pos=[11.98861289 15.        ],
  velocity=[-8.  0.],
  velocity_norm=[-1.  0.],
  speed=0.09544467966324248,
  cost=8.0,
  radius=0.0,
  speed_profile=([{'t_start': 0.0, 't_end': 2.5, 'action': 'accelerate', 'prof': 0.4, 's_start': 0.0, 's_end': 1.0, 'm': 1.25}, {'t_start': 2.5, 't_end': 8.0, 'action': 'cruise', 'prof': 1, 's_start': 1, 's_end': 1, 'm': 5.5}, {'t_start': 8.0, 't_end': 10.5, 'action': 'decelerate', 'prof': -0.4, 's_start': 1, 's_end': 0.0, 'm': 1.25}], 10.5),
  passed_time=0.2386116991581062
,  action start=15.811388300841895
,  action end=26.311388300841895
)
"""
    t3= """detectionObj(
  info=('N_12_14', 'N_4_14'),
  ostart=[12. 14.],
  oend=[ 4. 14.],
  pos=[11.83687729 14.        ],
  velocity=[-8.  0.],
  velocity_norm=[-1.  0.],
  speed=0.7003557437305936,
  cost=8.0,
  radius=0.0,
  speed_profile=([{'t_start': 0.0, 't_end': 1.0, 'action': 'accelerate', 'prof': 0.4, 's_start': 0.6, 's_end': 1.0, 'm': 0.8}, {'t_start': 1.0, 't_end': 7.4, 'action': 'cruise', 'prof': 1, 's_start': 1, 's_end': 1, 'm': 6.4}, {'t_start': 7.4, 't_end': 8.4, 'action': 'decelerate', 'prof': -0.4, 's_start': 1, 's_end': 0.6, 'm': 0.8}], 8.4),
  passed_time=6.8
,  action start=6.1000000000000005
,  action end=14.5
)
******************
detectionObj(
  info=('N_12_14', 'N_12_15'),
  ostart=[12. 14.],
  oend=[12. 15.],
  pos=[12.         14.01258909],
  velocity=[0. 1.],
  velocity_norm=[0. 1.],
  speed=0.10035574373059361,
  cost=1.0,
  radius=0.0,
  speed_profile=([{'t_start': 0.0, 't_end': 1.581138830084, 'action': 'accelerate', 'prof': 0.4, 's_start': 0.0, 's_end': 0.632455532034, 'm': 0.5}, {'t_start': 1.581138830084, 't_end': 3.162277660168, 'action': 'decelerate', 'prof': -0.4, 's_start': 0.632455532034, 's_end': 0.0, 'm': 0.5}], 3.162277660168379),
  passed_time=0.25088935932648404
,  action start=12.649110640673516
,  action end=15.811388300841895
)
"""
    plot_objects_with_distances(t2)
