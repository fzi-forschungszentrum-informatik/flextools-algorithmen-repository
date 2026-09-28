##################################
# Warehouse 35x21 Layout Config  #
##################################

IMAGE_FILE = './images/Matrix_Layout_22x22.PNG'
LAYOUT_NAME = 'matrix_22x22'
FORMS = ['grid', 'triangle', 'hexagonal']
DISTANCES = [[1, 0.5], [0.5], [0.5]]  # distances between nodes in grid
DISTANCES_TO_SIDE = [[0.5, 0.25], [0.25], [0.25]]  # distance to the upper left point in the image
AMR_RADIUS = 0.5
LENGTH = 22
WIDTH = 22

NUMBER_OF_NODES = 1000

MAX_REACH = 10000
NUMBER_OF_AMRS = [5, 10, 15, 20, 30]

LAYOUT_ID = 'map1'
PICKUP_TIME = 0
DELIVERY_TIME = 0
SEED = 9
TIMESTEP = 1
TASK_FREQUENCY_LIST = [1, 2, 5, 10]
NUMBER_OF_ORDERS_LIST = [200, 500]
ENDPOINT_DISTANCE_THRESHOLD = 0.9

SPLIT_X = []
SPLIT_Y = []

DISTANCE_BETWEEN_START_AND_GOAL = 5
DISTANCE_BETWEEN_START_POSITION = 1
MAX_TIME_START_POSITION = 60