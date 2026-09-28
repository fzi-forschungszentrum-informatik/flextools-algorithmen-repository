########################################################################################################################
# SINGULAR TESTING FOR MAPF ALGORITHMS
########################################################################################################################

GRID_TYPE = "square"  # triangular or square
GRID_WIDTH = 15
GRID_HEIGHT = 15

REMOVE_NODE_PROBABILITY = 0.1
RECONNECT_PROBABILITY = 0.5              # for cbs and ecbs -1, for i-ecbs between -1 and 1
RECONNECT_DIAGONAL_PROBABILITY = -1      # for cbs and ecbs -1, for i-ecbs between -1 and 1
NUMBER_OF_PATHS = 6
TEST_PP_LAYOUT_ID = "map1"
MAP_ID_DEFAULT = "map1"

########################################################################################################################
# Paths to the graph and start endpoint pairs which should be generated or loaded
########################################################################################################################
nb = 1
LIF_PATH = f"./data/test_{nb}.json"
PATH_PAIRS_FILE = f"./data/test_{nb}se.json"

########################################################################################################################
# Path Planning test configs
################################################################################################################
GENERATE_NEW_DATA = True                                # if false loads given paths above
SHOW_LIF = True                                          # shows LIF-graph and computed paths


########################################################################################################################
# LIF Generation Constants
########################################################################################################################
SPACING = 1.0
VEHICLE_TYPE_ID = "robot"
ROTATION_ALLOWED = True
MAX_SPEED = 1.0
