##################################
# Warehouse 35x21 Layout Config  #
##################################

IMAGE_FILE = './images/CrossDockingLayout.PNG'
LAYOUT_NAME = 'cross_docking'
FORMS = ['grid', 'triangle']
DISTANCES = [[1], [1]]  # distances between nodes in grid
DISTANCES_TO_SIDE = [[0.5], [0.5]]  # distance to the upper left point in the image
AMR_RADIUS = 0.5
LENGTH = 45
WIDTH = 45

NUMBER_OF_NODES = 1000

MAX_REACH = 10000
NUMBER_OF_AMRS = [10, 20, 30, 40, 50]

LAYOUT_ID = 'map1'
PICKUP_TIME = 0
DELIVERY_TIME = 0
SEED = 15
TIMESTEP = 1
TASK_FREQUENCY_LIST = [1, 2, 5, 10]
NUMBER_OF_ORDERS_LIST = [200, 500]
ENDPOINT_DISTANCE_THRESHOLD = 0.9

SPLIT_X = [11, 22, 33]
SPLIT_Y = []

DISTANCE_BETWEEN_START_AND_GOAL = 5
DISTANCE_BETWEEN_START_POSITION = 1
MAX_TIME_START_POSITION = 60
