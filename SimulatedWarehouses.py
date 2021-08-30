import random
from WarehouseMapping import NUM_OF_PLACES, Place, WarehouseMapping, LOCATIONS, SHELFS
from Env import Box
from abc import ABC

class SimulatedWarehouse(ABC):
    def __init__(self):
        """
        *The warehouse starts empty.
        *storage- list (which represents location) of list (which reperesnts shelf) of (Place, Box) = (location, shelf, id, quantity)
        emptySpaces- list of all empty Place() elements.
        """
        self.storage = []
        self.emptySpaces = []
        # popluate emptySpaces
        self.wMap = WarehouseMapping()
        for i in range(LOCATIONS):
            for j in range(SHELFS):
                self.emptySpaces.append(Place(i, j))

    def insertBoxes(self, boxes) -> float:
        prev_place = None
        total_distance = 0
        for box in boxes:
            cur_place = self.emptySpaces.pop(0)
            self.storage.append({'place':cur_place,'box': box})
            if prev_place == None:
                total_distance += self.wMap.fromEntrance(cur_place)
            else:
                total_distance += self.wMap.distance(prev_place, cur_place)
            prev_place = cur_place
        return self.wMap.distanceToTime(total_distance)


    def isEmpty(self, place):
        return place in (item[0] for item in self.storage)

    def removeProducts(self, boxesToRemove):
        total_distance = 0
        prev_place = None
        total_found = 0
        for box in boxesToRemove:
            found = False
            for item in self.storage:
                if item['box'].id == box.id and item['box'].quantity >= box.quantity:
                    item['box'].quantity -= box.quantity
                    found = True
                    total_found += 1
                    cur_place = item['place']
                    if prev_place:
                        total_distance += self.wMap.distance(prev_place, cur_place)
                    else:
                        total_distance += self.wMap.fromEntrance(cur_place)
                    prev_place = cur_place
                    if item['box'].quantity == 0:
                        self.storage.remove(item)
                        self.emptySpaces.append(item['place'])
                    break
            if not found:
                print('Not found')


        print(f'found {total_found} out of {len(boxesToRemove)}')
        return self.wMap.distanceToTime(total_distance)

    def organizeStorageList(self):
        pass

class GreedyWarehouse(SimulatedWarehouse):
    def __init__(self):
        super().__init__()
        self.emptySpaces.sort(key=self.wMap.fromEntrance)

    def organizeStorageList(self):
        self.storage.sort(key=self.wMap.fromEntrance)

class RandomWarehouse(SimulatedWarehouse):
    def __init__(self):
        super().__init__()
        self.emptySpaces = random.sample(self.emptySpaces, k=len(self.emptySpaces))

    def organizeStorageList(self):
        self.storage = random.sample(self.storage, k=len(self.storage))
