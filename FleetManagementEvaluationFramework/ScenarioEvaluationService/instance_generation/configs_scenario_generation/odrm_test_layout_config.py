##################################
# Warehouse 35x21 Layout Config  #
##################################

IMAGE_FILE = './images/Layout_Test.png'
LAYOUT_NAME = 'test_layout'
FORMS = ['prm', 'odrm', 'udrm']
DISTANCES = [[None], [None], [None]]  # distances between nodes in grid, no fix distance between nodes
DISTANCES_TO_SIDE = [[None], [None], [None]]
# distance to the upper left point in the image, no fix distance to side ODRM
AMR_RADIUS = 0.5  # for ODRM
LENGTH = 40
WIDTH = 40

NUMBER_OF_NODES = 200

MAX_REACH = 10000
NUMBER_OF_AMRS = [10, 20, 30, 40, 50]

LAYOUT_ID = 'map1'
PICKUP_TIME = 0
DELIVERY_TIME = 0
SEED = 1
TIMESTEP = 1
TASK_FREQUENCY_LIST = [1, 2, 5, 10]
NUMBER_OF_ORDERS_LIST = [200, 500]
ENDPOINT_DISTANCE_THRESHOLD = 1

SPLIT_X = []
SPLIT_Y = []

DISTANCE_BETWEEN_START_AND_GOAL = 5
DISTANCE_BETWEEN_START_POSITION = 1
MAX_TIME_START_POSITION = 60
