from Agent import getBestState, getRemovedPlaces
import WarehouseMapping
from WarehouseMapping import LOCATIONS, SHELFS, WarehouseMapping
from Env import Place, Env


class SmartWarehouse():
    def __init__(self):
        self.storage = []
        self.emptySpaces = []
        for i in range(LOCATIONS):
            for j in range(SHELFS):
                self.emptySpaces.append(Place(i, j))
    
    def insertBoxes(self, boxesToInsert):
        best_env, best_state, best_reward = getBestState(boxesToInsert, self)
        filledPlaces = best_env.getFiledPlaces()
        filledBoxes = best_env.getFiledBoxes()
        for filledPlace in filledPlaces:
            self.emptySpaces.remove(filledPlace)
        self.storage.extend(filledBoxes)
        wm = WarehouseMapping()
        return wm.distanceList(filledPlaces)
    
    def removeProducts(self, boxesToRemove):
        places, emptySpaces, RemovedStorage = getRemovedPlaces(boxesToRemove, self)
        self.emptySpaces.extend(emptySpaces)
        wm = WarehouseMapping()
        return wm.distanceList(places)
