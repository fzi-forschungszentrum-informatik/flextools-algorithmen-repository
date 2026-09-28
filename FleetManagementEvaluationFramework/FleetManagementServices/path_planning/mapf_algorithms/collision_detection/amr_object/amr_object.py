import numpy as np


class AmrObject:

    def __init__(self):
        ################################################################################################################
        # AMR specs
        self.position = 0
        self.radius = 0
        self.load = 0
        ################################################################################################################
        # Speed Profile
        self.initial_direction = np.array([0,0])
        self.initial_speed = 0
        # Speed Profiles Constants
        self.acceleration_max = 1            # TODO function of load ?
        self.deceleration_max = 1               # TODO function of load ?
        self.speed_max = 5                    # TODO function of load ?
        self.direction_change_speed_max = 1   # TODO function of load ?
        self.turning_duration = 10
        self.time_on_node_without_turning = 0
        ################################################################################################################
        # auto init
        self.initialise_amr_obj()

    def initialise_amr_obj(self):
        pass

    def get_end_speeds(self):
        return [self.speed_max, self.direction_change_speed_max, 0]
