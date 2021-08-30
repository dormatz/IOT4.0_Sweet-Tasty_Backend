import numpy as np
import itertools
from typing import List, Set, Dict, Tuple, Optional

AISLES = 8
SHELFS = 5
LOCATIONS_PER_AISLE = 100
FACTOR_LOC = 2
FACTOR_AISLE = 5
ENTRANCE = 300
PICKER_VELOCITY = 1.4  # m/s (3.6 km/h = 1 m/s)

LOCATIONS = AISLES*LOCATIONS_PER_AISLE
NUM_OF_PLACES = AISLES*SHELFS*LOCATIONS_PER_AISLE

class Place(object):
    def __init__(self, location, shelf):
        self.location = location
        self.shelf = shelf

    def __eq__(self, other_place):
        if isinstance(other_place, Place):
            return self.location == other_place.location and self.shelf == other_place.shelf
        return False

    def __str__(self):
        return '(' + str(self.location) + ', ' + str(self.shelf) + ')'

    def __repr__(self):
        return '(' + str(self.location) + ', ' + str(self.shelf) + ')'

    def inWarehouse(self):
        return 0 <= self.location < AISLES*LOCATIONS_PER_AISLE and 0 <= self.shelf < SHELFS

class WarehouseMapping(object):
    def __init__(self, calculate_loc2Dmatrix=False):
        # self.Locations2DMap = np.zeros((LOCATIONS_PER_AISLE*AISLES, LOCATIONS_PER_AISLE*AISLES))
        self._Shelfs1DMap = np.zeros(SHELFS)
        self.populate1D()  # if we have ~70000 calls to distance(), we better of also populating 2D map on init.
        self.calculate_loc2Dmatrix = calculate_loc2Dmatrix
        if(calculate_loc2Dmatrix):
            self.populate2D()  # for or-tools tsp solver



    def populate1D(self):
        it = np.nditer(self._Shelfs1DMap, op_flags=['readwrite'], flags=['f_index'])
        for x in it:
            x[...] = it.index * 2
            if (it.index == 0):
                x[...] += 1
            if (it.index >= 2):
                x[...] += 1

    def populate2D(self):
        self._Loc2DMap = np.zeros((LOCATIONS,LOCATIONS))
        _range = list(range(LOCATIONS))
        for (i,j) in itertools.product(_range,_range):
            self._Loc2DMap[i][j] = self.distance(Place(i, 4), Place(j, 4), walk_dist=True)

    """"including shelfs height!"""
    def getLoc2DMapForTSP(self, places: list):
        places.append(Place(-1, 1))  # dummy location for end
        places.insert(0, Place(ENTRANCE, 1))  # entrance node for start
        locs = [p.location for p in places]
        index_to_locs = {index: loc for index, loc in enumerate(locs)}
        n = len(places)
        map = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if places[i].location==-1 or places[j].location==-1:
                    map[i, j]=0
                    continue
                map[i, j] = self.distance(places[i], places[j], walk_dist=False)
        return (map, index_to_locs)


    def getLoc2DMap(self):
        assert(self.calculate_loc2Dmatrix)
        return self._Loc2DMap


    def fromEntrance(self, place: Place):

        #  return (place.location % LOCATIONS_PER_AISLE) + self._Shelfs1DMap[place.shelf]
        return self.distance(Place(ENTRANCE, 0), place, walk_dist=True) + self._Shelfs1DMap[place.shelf]

    """   def distance(self, place1: Place, place2: Place):
        return self.Locations2DMap[place1.location][place2.location] + \
               self.Shelfs1DMap[place1.shelf] + \
               self.Shelfs1DMap[place2.shelf]
    """

    def distance(self, place1: Place, place2: Place, walk_dist=False):  # walk_dist takes only locations into calc
        assert place1.inWarehouse() and place2.inWarehouse()
        # L2 is the bigger location, we calculate L2 -> L1 distance
        L2 = place1.location if place1.location > place2.location else place2.location
        L1 = place1.location if L2 == place2.location else place2.location

        aisle1 = int(L1 / LOCATIONS_PER_AISLE)
        aisle2 = int(L2 / LOCATIONS_PER_AISLE)

        if(L2==L1):
            return abs(self._Shelfs1DMap[place1.shelf] - self._Shelfs1DMap[place2.shelf]) if not walk_dist else 0

        if(aisle2 == aisle1):
            return self._Shelfs1DMap[place1.shelf] + FACTOR_LOC * (L2 - L1) + self._Shelfs1DMap[place1.shelf] \
                if not walk_dist else FACTOR_LOC * (L2 - L1)

        #not same aisle
        if (L1 % LOCATIONS_PER_AISLE) > ((LOCATIONS_PER_AISLE-1) - (L2 % LOCATIONS_PER_AISLE)):
            # shorter to go from far end of aisle
            leg1 = ((LOCATIONS_PER_AISLE-1) - (L2 % LOCATIONS_PER_AISLE))
            went_from_end = True
        else:
            # shorter to go from start of aisle
            leg1 = (L2 % LOCATIONS_PER_AISLE)
            went_from_end = False

        leg2 = (aisle2 - aisle1)

        leg3 = ((LOCATIONS_PER_AISLE-1) - (L1 % LOCATIONS_PER_AISLE)) if went_from_end else (L1 % LOCATIONS_PER_AISLE)

        calculated_dist = (FACTOR_LOC * leg1) + (FACTOR_AISLE * leg2) + (FACTOR_LOC * leg3) # factoring to try and mimic real distance
        if not walk_dist:
            calculated_dist += self._Shelfs1DMap[place2.shelf] + self._Shelfs1DMap[place1.shelf]
        return calculated_dist

    def distanceToTime(self, d):
        return float(d)/float(PICKER_VELOCITY)

    def distanceList(self, places: List[Place]):
        total_distance = 0
        for i in range(len(places)):
            if i == 0:
                total_distance += self.fromEntrance(places[i])
            else:
                if i != len(places)-1:
                    total_distance += self.distance(places[i], places[i+1], walk_dist=True)
        return self.distanceToTime(total_distance)
"""
if __name__ == '__main__':
    mapping = WarehouseMapping(calculate_loc2Dmatrix=True)
    print(mapping.fromEntrance(Place(202, 2)))
    print(mapping.distance(Place(206, 3), Place(204, 4)))
    mat = mapping.getLoc2DMap()
    print(mat)
"""