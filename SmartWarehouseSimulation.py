from numpy import empty
from Agent import getBestState, getRemovedPlaces
import WarehouseMapping
from WarehouseMapping import LOCATIONS, SHELFS, WarehouseMapping
from Env import Place, Env, Warehouse
from copy import deepcopy
import config


class SmartWarehouse(Warehouse):
    def __init__(self):
        self.storage = []
        self.emptySpaces = []
        for i in range(LOCATIONS):
            for j in range(SHELFS):
                self.emptySpaces.append(Place(i, j))
        wm = WarehouseMapping()
        self.emptySpaces.sort(key=lambda place: wm.fromEntrance(place))
        self.updatedStorage = []
        self.addToEmptySpaces = []
    
    def insertBoxes(self, boxesToInsert):
        wm = WarehouseMapping()
        if len(self.storage) < config.LIMIT_FOR_SMART_USE:
            placesToFill = self.emptySpaces[0:len(boxesToInsert)]
            for i, place in enumerate(placesToFill):
                self.storage.append({"place":place, "box":boxesToInsert[i], 'distanceFromEntrance':wm.fromEntrance(place)})
            self.emptySpaces[0:len(boxesToInsert)] = []
            return wm.totalTimeList(placesToFill)

        self.storage.sort(key=lambda obj: obj['distanceFromEntrance'])
        fullEmptySpaces = deepcopy(self.emptySpaces)
        self.emptySpaces = self.emptySpaces[0:config.EMPTY_SPACE_LEN_FACTOR*len(boxesToInsert)]
        best_env, _, _ = getBestState(boxesToInsert, self)
        self.emptySpaces = fullEmptySpaces
        placesToFill = best_env.getFilledPlaces()
        filledBoxes = best_env.getFilledBoxes()
        for filledPlace in placesToFill:
            self.emptySpaces.remove(filledPlace)
        self.storage.extend(filledBoxes)
        return wm.totalTimeList(placesToFill)
    
    def removeProductsList(self, boxesToRemove):
        removedPlaces = getRemovedPlaces(boxesToRemove, self)
        if removedPlaces is None:
            return 0
        places, emptySpaces, updatedStorage = removedPlaces
        self.emptySpaces.extend(emptySpaces)
        return WarehouseMapping().totalTimeList(places)
