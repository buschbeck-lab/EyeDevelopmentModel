# from epithelium_backend.Epithelium import Epithelium
from math import inf


class Furrow:
    """
    Simulates a morphogenetic furrow. Stores and maintains all information related to the
    morphogenetic furrow (movement speed, position, etc...). Used to apply a sequence of development
    events to an Epithelium.
    """

    def __init__(self,
                 position: float = 0,
                 velocity: float = 0,
                 events: list = None) -> None:
        """Initialize this instance of Furrow.
        :param position: The horizontal position of this Furrow.
        :param velocity: how many units the furrow moves in one 'tick'.
        :param events: Specialization events (stored as callable objects) triggered by the progression of the furrow.
        """
        self.position = position  # type: float
        self.velocity = velocity  # type: float
        self.events = events  # type: list

        self.last_position = inf

        if self.events is None:
            self.events = []

    def advance(self, distance: float = 0) -> None:
        """
        Moves the furrow forward by the specified amount.
        :param distance: how far to move this Furrow
        """
        self.last_position = self.position
        self.position -= distance

    def update(self, epithelium) -> None:
        """
        Simulates this Furrow for one tick.
        :param epithelium: The epithelium to be updated by this furrow.
        """

        # move the furrow forward
        self.advance(self.velocity)

        # run events on the cells
        for event in self.events:
            event(self.last_position, self.position, epithelium)
