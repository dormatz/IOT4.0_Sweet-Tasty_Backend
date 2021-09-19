from Agent import getBestState, getRemovedPlaces
import WarehouseMapping
from WarehouseMapping import LOCATIONS, SHELFS, WarehouseMapping
from Env import Place, Env, Warehouse
from copy import deepcopy


class SmartWarehouse(Warehouse):
    def __init__(self):
        self.storage = []
        self.emptySpaces = []
        for i in range(LOCATIONS):
            for j in range(SHELFS):
                self.emptySpaces.append(Place(i, j))
    
    def insertBoxes(self, boxesToInsert):
        wm = WarehouseMapping()
        fullEmptySpaces = deepcopy(self.emptySpaces)
        self.emptySpaces.sort(key=lambda obj: wm.fromEntrance(obj))
        self.emptySpaces = self.emptySpaces[0:2*len(boxesToInsert)]
        best_env, _, _ = getBestState(boxesToInsert, self)
        self.emptySpaces = fullEmptySpaces
        filledPlaces = best_env.getFilledPlaces()
        filledBoxes = best_env.getFilledBoxes()
        for filledPlace in filledPlaces:
            self.emptySpaces.remove(filledPlace)
        self.storage.extend(filledBoxes)
        wm = WarehouseMapping()
        return wm.distanceList(filledPlaces)
    
    def removeProducts(self, boxesToRemove):
        places, emptySpaces, updatedStorage = getRemovedPlaces(boxesToRemove, self)
        self.emptySpaces.extend(emptySpaces)
        self.storage = updatedStorage
        wm = WarehouseMapping()
        return wm.distanceList(places)
