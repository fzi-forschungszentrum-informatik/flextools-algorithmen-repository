import math
import random
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib
import cv2

matplotlib.use("TkAgg")


def euclidean_dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dynamic_cluster_radius(length: float, width: float, num_agents: int, factor: float = 0.8) -> float:
    area = max(length * width, 1e-6)
    return factor * math.sqrt(area / max(num_agents, 1))


def dynamic_min_distance(length: float, width: float, num_agents: int, factor: float = 1.0) -> float:
    area = max(length * width, 1e-6)
    return factor * math.sqrt(area / max(num_agents, 1))


def dynamic_num_clusters(num_agents: int, min_clusters: int = 2) -> int:
    return max(min_clusters, max(1, num_agents // 4))


def collect_traversable_coords(image_file: str, length: float, width: float, black_threshold: int = 10) -> List[Tuple[float, float]]:

    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_file}")


    image_h, image_w = img.shape
    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width

    coordinates = []

    for y_px in range(image_h):
        for x_px in range(image_w):
            pixel_value = img[y_px, x_px]
            if pixel_value > black_threshold:  # no black value
                x_m = x_px / px_per_meter_x
                y_m = y_px / px_per_meter_y
                coordinates.append((x_m, y_m))
    if not coordinates:
        raise ValueError("No traversable coordinates found in image (check threshold/walls).")
    return coordinates


def sample_with_min_distance(coords: List[Tuple[float, float]], num_points: int, min_dist: float,
                             max_attempts: int = 10000) -> List[Tuple[float, float]]:
    selected = []
    attempts = 0
    while len(selected) < num_points and attempts < max_attempts:
        cand = random.choice(coords)
        if all(euclidean_dist(cand, s) >= min_dist for s in selected):
            selected.append(cand)
        attempts += 1

    if len(selected) < num_points:
        remaining = [c for c in coords if c not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:(num_points - len(selected))])
    return selected


def clustered_sampling(coords: List[Tuple[float, float]], num_points: int, cluster_radius: float,
                       max_attempts: int = 20000) -> List[Tuple[float, float]]:
    selected = []
    attempts = 0
    center = random.choice(coords)
    cx, cy = center
    while len(selected) < num_points and attempts < max_attempts:
        cand = random.choice(coords)
        if (cand[0] - cx)**2 + (cand[1] - cy)**2 <= cluster_radius**2:
            selected.append(cand)
        attempts += 1
    if len(selected) < num_points:
        sorted_by_dist = sorted(coords, key=lambda p: euclidean_dist(p, center))
        for p in sorted_by_dist:
            if p not in selected:
                selected.append(p)
                if len(selected) >= num_points:
                    break
    return selected


def multi_cluster_sampling(coords: List[Tuple[float, float]], num_points: int,
                           num_clusters: int, cluster_radius: float) -> List[Tuple[float, float]]:
    centers = []
    tries = 0
    while len(centers) < num_clusters and tries < 5000:
        c = random.choice(coords)
        if all(euclidean_dist(c, existing) >= cluster_radius * 0.5 for existing in centers):
            centers.append(c)
        tries += 1
    if not centers:
        centers = [random.choice(coords) for _ in range(num_clusters)]

    selected = []
    per_cluster = [0] * len(centers)
    for i in range(num_points):
        idx = i % len(centers)
        cx, cy = centers[idx]
        found = False
        for _ in range(2000):
            cand = random.choice(coords)
            if (cand[0] - cx)**2 + (cand[1] - cy)**2 <= cluster_radius**2:
                selected.append(cand)
                per_cluster[idx] += 1
                found = True
                break
        if not found:
            nearest = min(coords, key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
            selected.append(nearest)
            per_cluster[idx] += 1
    unique_sel = []
    for p in selected:
        if p not in unique_sel:
            unique_sel.append(p)
    if len(unique_sel) < num_points:
        rem = [c for c in coords if c not in unique_sel]
    return unique_sel[:num_points]


def assign_goals_with_min_task_length(starts: List[Tuple[float, float]], coords: List[Tuple[float, float]],
                                      min_length: float, strategy: str = 'near_start') -> List[Tuple[float, float]]:
    goals = []
    coords_np = coords


    for sx, sy in starts:
        if strategy == 'near_start':
            candidates = [c for c in coords_np if euclidean_dist((sx, sy), c) >= min_length and euclidean_dist((sx, sy), c) <= min_length * 2]
            if not candidates:
                candidates = [c for c in coords_np if euclidean_dist((sx, sy), c) >= min_length]
        elif strategy == 'far_from_start':
            sorted_by_far = sorted(coords_np, key=lambda c: -euclidean_dist((sx, sy), c))
            candidates = [c for c in sorted_by_far if euclidean_dist((sx, sy), c) >= min_length]
        elif strategy == 'inter_cluster':
            candidates = [c for c in coords_np if euclidean_dist((sx, sy), c) >= min_length]
            candidates = sorted(candidates, key=lambda c: euclidean_dist((sx, sy), c), reverse=True)
        else:
            candidates = [c for c in coords_np if euclidean_dist((sx, sy), c) >= min_length]


        if not candidates:
            goals.append(random.choice(coords_np))
        else:
            goals.append(random.choice(candidates))

    return goals

def generate_agents(image_file: str,
                    length: float,
                    width: float,
                    num_agents: int,
                    difficult: str = 'medium',
                    min_task_length: float = 1.0,
                    goal_strategy: str = 'near_start',
                    visualize: bool = False,
                    random_seed: Optional[int] = None) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    random.seed(random_seed)

    coords = collect_traversable_coords(image_file, length, width)

    cluster_r = dynamic_cluster_radius(length, width, num_agents, factor=0.8)
    min_d = dynamic_min_distance(length, width, num_agents, factor=1.0)
    num_clusters = dynamic_num_clusters(num_agents)

    if difficult == "easy":
        start_points = sample_with_min_distance(coords, num_agents, min_dist=min_d)

    elif difficult == "medium":
        start_points = multi_cluster_sampling(coords,
                                              num_points=num_agents,
                                              num_clusters=num_clusters,
                                              cluster_radius=cluster_r)

    elif difficult == "hard":
        start_points = clustered_sampling(coords,
                                          num_points=num_agents,
                                          cluster_radius=cluster_r)
    else:
        raise ValueError("difficulty must be: easy, medium, hard")

    goal_points = assign_goals_with_min_task_length(start_points, coords, min_length=min_task_length,
                                                    strategy=goal_strategy)

    if visualize:
        try:

            xs = [p[0] for p in coords]
            ys = [p[1] for p in coords]
            sx = [p[0] for p in start_points]
            sy = [p[1] for p in start_points]
            gx = [p[0] for p in goal_points]
            gy = [p[1] for p in goal_points]

            plt.figure(figsize=(8, 6))
            plt.scatter(xs, ys, s=1, alpha=0.2, label='free')
            plt.scatter(sx, sy, s=30, marker='o', label='start')
            plt.scatter(gx, gy, s=30, marker='x', label='goal')
            for a, b in zip(start_points, goal_points):
                plt.plot([a[0], b[0]], [a[1], b[1]], linewidth=0.5, alpha=0.6)
            plt.title(f"starts/goals: {difficult} | clusters={num_clusters} | cluster_r={cluster_r:.2f}")
            plt.legend()
            plt.gca().invert_yaxis()
            plt.xlabel('x [m]')
            plt.ylabel('y [m]')
            plt.axis('equal')
            plt.show()
        except Exception as e:
            raise("Error: Visualization:", e)

    return start_points, goal_points

if __name__ == '__main__':
    starts, goals = generate_agents(image_file='../images/Warehouse_35x21.PNG',
                                    length=35,
                                    width=21,
                                    num_agents=20,
                                    difficult='hard',
                                    min_task_length=10,
                                    goal_strategy='inter_cluster',
                                    visualize=True,
                                    random_seed=42
                                    )
