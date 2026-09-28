from abc import abstractmethod, ABC

from data.data_structures.extended_graph import ExtendedGraph


class CollisionDetectionInterface(ABC):

    def __init__(self, graph=None):
        self.graph: ExtendedGraph | None = graph

    @abstractmethod
    def get_empty_constraint_class(self):
        """
        !!! Must be implemented !!!
        :return: the structure needed by the CBS Variation to put into the CBS-nodes 'constraint' field
        """

    @abstractmethod
    def get_collision_detection_function(self):
        """
        !!! Must be implemented !!!
        :return: returns the wanted collision detection function
        """

    @abstractmethod
    def get_insertion_function(self):
        """
        !!! Must be implemented !!!
        :return: return the function which inserts the collision into the wanted structure
        """

    @abstractmethod
    def get_violates_constraints(self, constraints):
        """
        !!! Must be implemented !!!
        :return: returns the violates_constraints fct function used in low level
        """

    @abstractmethod
    def get_has_infinite_interval(self, constraints):
        """
        !!! Must be implemented !!!
        :return: returns the has inf interval fct function used in low level
        """

    @abstractmethod
    def get_colliding_agents(self, collision):
        """:returns: correct data from collision variant"""
