#!/usr/bin/env python

from WarehouseMapping import Place, WarehouseMapping, SHELFS, LOCATIONS_PER_AISLE, AISLES
import json
import os
from firebase_con import getEmptySpaceCollectionFirebase, getStorageCollectionFirebase, updateStorageCollectionFirebase, updateEmptySpaces
from copy import deepcopy
from typing import List, Dict, Tuple, Optional

class Box(object):
    def __init__(self, id=-1, quantity=0):
        self.id = id
        self.quantity = quantity
    
    def removeProducts(self, quantity):
        self.quantity -= quantity
    
    def isEmpty(self):
        return self.quantity == 0

    def id(self):
        return self.id

    def __str__(self):
        return '(' + str(self.id) + ', ' + str(self.quantity) + ')'

    def __repr__(self):
        return '(' + str(self.id) + ', ' + str(self.quantity) + ')'


class State(object):
    def __init__(self, boxesToInsert: List[Box], warehouse=None):
        """
        WareHouse- Warehouse element
        insertedBoxes- list of dicts of {Place, Box} elements
        boxesToInsert- list of Box elements
        """
        self.warehouse = Warehouse(len(boxesToInsert)*2) if warehouse is None else warehouse
        self.boxesToInsert = deepcopy(boxesToInsert)
        self.insertedBoxes = []

    def isDone(self):
        return len(self.boxesToInsert) == 0

    def insertBox(self, place):
        wm = WarehouseMapping()
        box = self.boxesToInsert[0]
        self.warehouse.insertBox(place, box)
        self.insertedBoxes.append({"place":place, "box":box, 'distanceFromEntrance':wm.fromEntrance(place)})
        self.boxesToInsert.pop(0)


class Warehouse(object):
    def __init__(self, size: int, itemsToRemove: List[Box]=None):
        """
        *The warehouse starts empty.
        *storage- list of dictionaries with keys -  place: Place(), box:Box()
        emptySpaces- list of all empty Place() elements.
        """
        self.storage = []
        if itemsToRemove:
            ids = [item.id for item in itemsToRemove]
            docs = getStorageCollectionFirebase(ids)
        else:
            docs = getStorageCollectionFirebase()
        for doc in docs:
            item = doc.to_dict()
            self.storage.append({'place':Place(item['location'],item['shelf']), 'box':Box(item['id'], item['quantity']), 'distanceFromEntrance':item['distanceFromEntrance']})
        self.emptySpaces = []
        docs = getEmptySpaceCollectionFirebase(size) if size != 0 else []
        for doc in docs:
            item = doc.to_dict()
            self.emptySpaces.append(Place(item['location'], item['shelf']))
        self.addToEmptySpaces = []
        self.updatedStorage = []

    def insertBox(self, place, box):
        wm = WarehouseMapping()
        self.storage.append({'place':place, 'box':box, 'distanceFromEntrance':wm.fromEntrance(place)})
        for emptySpace in self.emptySpaces:
            if emptySpace == place:
                self.emptySpaces.remove(emptySpace)
                return
    
    def isEmpty(self, place):
        return place in (item[0] for item in self.storage)
    
    def removeProducts(self, place, quantity):
        for item in self.storage:
            if item['place'] == place:
                item['box'].quantity -= quantity
                if item['box'].quantity == 0:
                    self.storage.remove(item)
                    self.addToEmptySpaces.append(place)
                else:
                    self.updatedStorage.append(item)
                return

class Env(object):
    def __init__(self, BoxesToInsert: List[Box], warehouse=None):
        self.state = State(BoxesToInsert, warehouse)
        actions = sorted([(emptyPlace, WarehouseMapping().fromEntrance(emptyPlace)) for emptyPlace in self.state.warehouse.emptySpaces], key=lambda obj: obj[1])
        self.actions = [action[0] for action in actions[:len(BoxesToInsert)*10]]
    
    def step(self, action):
        self.state.insertBox(action)
        self.actions.remove(action)

    def getFilledPlaces(self):
        return [insertedBox["place"] for insertedBox in self.state.insertedBoxes]

    def getFilledBoxes(self):
        return self.state.insertedBoxes

def saveEmptySpaces(FiledPlaces: List[Place], remove=True):
    for place in FiledPlaces:
        if remove:
            updateEmptySpaces(place, delete=True)
        else:
            updateStorageCollectionFirebase(place, None, delete=True)
            updateEmptySpaces(place)

def saveStorage(FiledBoxes: List[Box]):
    for box in FiledBoxes:
        updateStorageCollectionFirebase(box['place'], box['box'])
