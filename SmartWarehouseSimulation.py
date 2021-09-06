from Agent import getBestState
import WarehouseMapping
from WarehouseMapping import LOCATIONS, SHELFS
from Env import Place, Env


class SmartWarehouse():
    def __init__(self):
        self.storage = []
        self.emptySpaces = []
        for i in range(LOCATIONS):
            for j in range(SHELFS):
                self.emptySpaces.append(Place(i, j))
    
    def insertBoxes(self, boxes):
        best_env, best_state, best_reward = getBestState(boxesToInsert, self)
        filledPlaces = best_env.getFiledPlaces()
        filledBoxes = best_env.getFiledBoxes()
        for filledPlace in filledPlaces:
            self.emptySpaces.remove(filledPlace)
        self.storage.extend(filledBoxes)
        wm = WarehouseMapping()
        return wm.distanceList(filledPlaces)
    
    def removeProducts(self, boxes):
        places, emptySpaces, RemovedStorage = getRemovedPlaces(boxesToRemove, self)
        self.emptySpaces.extend(emptySpaces)
        wm = WarehouseMapping()
        return wm.distanceList(places)
