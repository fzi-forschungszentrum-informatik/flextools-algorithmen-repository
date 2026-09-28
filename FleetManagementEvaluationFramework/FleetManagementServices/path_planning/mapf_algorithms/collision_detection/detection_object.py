import numpy as np

from config.config_file import AMR_RADIUS


class DetectionObj:
    def __init__(self, info):
        self.info = info
        self.ostart = None
        self.oend = None
        self.pos = None
        self.velocity = None
        self.velocity_norm = None
        self.speed = None  # used with constant speeds as speed, with varying speed this is only speed at start of calculation
        self.cost = None
        self.radius = AMR_RADIUS
        ################################################################################################################
        # variables only used by varying speeds
        ################################################################################################################
        self.speed_profile = None
        self.passed_time = None
        self.action_start = None
        self.action_end = None
        self.solver_start_time = None
        self.solver_end_time = None

    def __str__(self):
        return (
            f"detectionObj(\n"
            f"  info={self.info},\n"
            f"  ostart={self.ostart},\n"
            f"  oend={self.oend},\n"
            f"  pos={self.pos},\n"
            f"  velocity={self.velocity},\n"
            f"  velocity_norm={self.velocity_norm},\n"
            f"  speed={self.speed},\n"
            f"  cost={self.cost},\n"
            f"  radius={self.radius},\n"
            f"  speed_profile={self.speed_profile},\n"
            f"  passed_time={self.passed_time}\n,"
            f"  action start={self.action_start}\n,"
            f"  action end={self.action_end}\n"
            f")"
        )

    def new_velocity(self, vel):
        self.velocity = vel
        norm = np.linalg.norm(self.velocity)
        if norm == 0:
            self.velocity_norm = vel
        else:
            self.velocity_norm = vel / norm