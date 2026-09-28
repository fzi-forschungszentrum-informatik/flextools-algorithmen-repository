import numpy as np


class Zone3D:
    def __init__(self, corners, t_start, t_end):
        self.corners = corners
        self.t_start = t_start
        self.t_end = t_end
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        self.aabb = (min(xs), min(ys), max(xs), max(ys))

    def __str__(self):
        return (
            f"Zone3D:,\n"
            f"start:   {self.t_start},\n"
            f"end:     {self.t_end},\n"
            f"corners: {[(float(x[0]), float(x[1])) for x in self.corners]}"
        )
