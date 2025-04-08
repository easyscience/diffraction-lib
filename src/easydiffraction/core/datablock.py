from abc import ABC, abstractmethod

from easydiffraction.core.component import (StandardComponent,
                                            IterableComponent)

class Datablock(ABC):
    """
    Base class for Sample Model and Experiment data blocks.
    """

    def components(self):
        """
        Returns a list of both standard and iterable components in the
        data block.
        """
        attr_objs = []
        for attr_name in dir(self):
            attr_obj = getattr(self, attr_name)
            if isinstance(attr_obj, (StandardComponent,
                                     IterableComponent)):
                attr_objs.append(attr_obj)
        return attr_objs
