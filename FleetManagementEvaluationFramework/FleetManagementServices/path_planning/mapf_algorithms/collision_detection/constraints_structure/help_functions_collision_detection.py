import math

import numpy as np


def get_oriented_bounding_box_axes(corners):
    """
    corners: list of tuples (x,y) in order
    return: list of axes (unit vectors)
    """
    # parallel axis of the rectangle
    ax1 = (corners[1][0] - corners[0][0], corners[1][1] - corners[0][1])
    ax2 = (corners[3][0] - corners[0][0], corners[3][1] - corners[0][1])
    # normalize the axis
    def normalize(v):
        length = math.hypot(v[0], v[1])
        return (v[0]/length, v[1]/length)
    return [normalize(ax1), normalize(ax2)]


def project_to_axis(corners, axis):
    """
    projections of the 0-dim faces (corners) onto the edges
    return: (min, max)
    """
    dots = [corner[0]*axis[0] + corner[1]*axis[1] for corner in corners]
    return min(dots), max(dots)


def obb_vs_obb(corners1, corners2):
    """
    Separating axis theorem collision check for two axis
    corners = list of tuples (x,y)
    """
    axes = get_oriented_bounding_box_axes(corners1) + get_oriented_bounding_box_axes(corners2)
    for axis in axes:
        min1, max1 = project_to_axis(corners1, axis)
        min2, max2 = project_to_axis(corners2, axis)
        if max1 < min2 or max2 < min1:
            return False
    return True


def point_to_oriented_bounding_box_distance(px, py, corners):
    """
    minimal distance to OBB
    """
    # projection and test all segments
    min_dist = float('inf')
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i+1) % 4]
        # dist of point to segment
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            d = math.hypot(px - x1, py - y1)
        else:
            t = max(0, min(1, ((px - x1)*dx + (py - y1)*dy)/(dx*dx + dy*dy)))
            projx = x1 + t*dx
            projy = y1 + t*dy
            d = math.hypot(px - projx, py - projy)
        if d < min_dist:
            min_dist = d
    return min_dist


