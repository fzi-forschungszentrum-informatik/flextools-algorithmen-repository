from abc import ABC, abstractmethod


class LowLevelSearchInterface(ABC):
    def __init__(self, *args, **kwargs):
        """
        !!! Must be implemented !!!
        :param args:
        :param kwargs:
        """

    @abstractmethod
    def compute_path(self):
        """
        !!! Must be implemented !!!
        :return: path, cost, expanded nodes a star
        """

