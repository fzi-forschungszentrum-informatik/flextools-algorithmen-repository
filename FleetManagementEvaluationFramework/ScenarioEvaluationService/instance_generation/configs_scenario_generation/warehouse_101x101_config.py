##################################
# Warehouse 35x21 Layout Config  #
##################################

IMAGE_FILE = './images/Warehouse_101x101.PNG'
LAYOUT_NAME = 'warehouse_101x101'
FORMS = ['grid', 'triangle',]
DISTANCES = [[1], [1]]  # distances between nodes in grid
DISTANCES_TO_SIDE = [[0.5], [0.5]]  # distance to the upper left point in the image
AMR_RADIUS = 0.5
LENGTH = 101
WIDTH = 101

NUMBER_OF_NODES = 1000

MAX_REACH = 10000
NUMBER_OF_AMRS = [10, 20, 30, 40, 50, 70, 100, 150]

LAYOUT_ID = 'map1'
PICKUP_TIME = 0
DELIVERY_TIME = 0
SEED = 11
TIMESTEP = 1
TASK_FREQUENCY_LIST = [1, 2, 5, 10]
NUMBER_OF_ORDERS_LIST = [200, 500, 1000]
ENDPOINT_DISTANCE_THRESHOLD = 0.9


SPLIT_X = []
SPLIT_Y = []

DISTANCE_BETWEEN_START_AND_GOAL = 5
DISTANCE_BETWEEN_START_POSITION = 1
MAX_TIME_START_POSITION = 60