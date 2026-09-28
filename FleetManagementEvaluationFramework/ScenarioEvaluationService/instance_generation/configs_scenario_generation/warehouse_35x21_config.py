##################################
# Warehouse 35x21 Layout Config  #
##################################

IMAGE_FILE = './images/Warehouse_35x21.PNG'
LAYOUT_NAME = 'warehouse_35x21'
FORMS = ['grid', 'triangle', 'hexagonal']
DISTANCES = [[1, 0.5], [1, 0.5], [0.5]]  # distances between nodes in grid, no fix distance between nodes
DISTANCES_TO_SIDE = [[0.5, 0.25], [0.5, 0.25], [0.25]]  # distance to the upper left point in the image
AMR_RADIUS = 0.5  # for ODRM
LENGTH = 35
WIDTH = 21

NUMBER_OF_NODES = 1000

MAX_REACH = 10000
NUMBER_OF_AMRS = [10, 20, 30, 40, 50]

LAYOUT_ID = 'map1'
PICKUP_TIME = 0
DELIVERY_TIME = 0
SEED = 1
TIMESTEP = 1
TASK_FREQUENCY_LIST = [1, 2, 5, 10]
NUMBER_OF_ORDERS_LIST = [200, 500]
ENDPOINT_DISTANCE_THRESHOLD = 0.9

SPLIT_X = []
SPLIT_Y = []

DISTANCE_BETWEEN_START_AND_GOAL = 5
DISTANCE_BETWEEN_START_POSITION = 1
MAX_TIME_START_POSITION = 60
