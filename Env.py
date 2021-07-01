#!/usr/bin/env python
import pyrebase
from WarehouseMapping import Place, WarehouseMapping, AISLES, SHELFS, LOCATIONS_PER_AISLE, LOCATIONS, NUM_OF_PLACES
import json
import os
import ast

DIR_EMPTY_SPACES = "emptySpaces.txt"
DIR_STORAGE = "storage.txt"

class State(object):
    def __init__(self, warehouse, boxesToInsert):
        """
        products- list [ Box ]

        """
        self.warehouse = warehouse
        self.boxesToInsert = boxesToInsert
        self.insertedBoxes = []

    def isDone(self):
        if len(self.boxesToInsert) == 0:
            return True
        return False

    def insertBox(self, place, reward):
        box = self.boxesToInsert[0]
        self.warehouse.insertBox(place, box)
        self.insertedBoxes.append({"location":place.location, "shelf":place.shelf, "id":box.id})
        self.boxesToInsert.remove(box)

class Box(object):
    def __init__(self, id=-1, quantity=0):
        self.id = id
        self.quantity = quantity
    
    def removeProducts(self, quantity):
        self.quantity -= quantity
    
    def isEmpty(self):
        return self.quantity == 0

class Warehouse(object):
    def __init__(self):
        """
        *The warehouse starts empty.
        """
        self.storage = [[Box()]*SHELFS]*LOCATIONS if not os.isfile(DIR_STORAGE) else recoverStorage()
        self.emptySpaces = [Place(location, shelf) for shelf in range(SHELFS) for location in range(LOCATIONS)] if not os.isfile(DIR_EMPTY_SPACES) else recoverEmptySpaces()

    def insertBox(self, place, box):
        self.storage[place.location][place.shelf] = box
        self.emptySpaces.remove(place)
    
    def isEmpty(self, place):
        return self.storage[place.location][place.shelf].id == -1
    
    def removeProducts(self, place, quantity):
        product = self.storage[place.location][place.shelf]
        product.removeProducts(quantity)
        if product.isEmpty():
            self.storage[place.location][place.shelf] = Box()
            self.emptySpaces.append(place)

class Env(object):
    def __init__(self, BoxesToInsert):
        warehouse = Warehouse()
        #set warehouse from firebase
        self.state = State(warehouse, BoxesToInsert)
        sorted([(Place(location, shelf), WarehouseMapping().fromEntrance(Place(location, shelf))) \
                                   for shelf in range(SHELFS) for location in range(LOCATIONS)], key=lambda place: place[2])
        self.actions = warehouse[:len(BoxesToInsert)*10]
    
    def step(self, action):
        self.state.insertBox(action)
        self.actions.remove(action)
        return self.state


def saveEmptySpaces(listOfPlaces):
    fd = open(DIR_EMPTY_SPACES, 'w+')
    for place in listOfPlaces:
        place_json = json.dumps(place.__dict__)
        fd.write(place_json)
        fd.write(", ")
    fd.close()

def recoverEmptySpaces():
    listOfPlaces = []
    fd = open(DIR_EMPTY_SPACES, 'r')
    data_string = fd.read()
    data_list = ast.literal_eval(data_string)
    for item in data_list:
        listOfPlaces.append(Place(item["location"], item["shelf"]))
    fd.close()
    return listOfPlaces   

def saveStorage(storage: list[list[Box]]):
    fd = open(DIR_STORAGE, "w+")
    for i in storage:
        fd.write( "[")    
        for j in i:
            j_l = json.dumps(j.__dict__)
            fd.write(j_l)
            fd.write( " , ")
        fd.write( " ] , ")
    fd.close()

def recoverStorage():
    fd = open(DIR_STORAGE, "r")
    storageString = fd.read()
    fd.close()
    locationsTuple = ast.literal_eval(storageString)
    storage = []
    for i, location in enumerate(locationsTuple):
        shelfList = []
        for box in location:
            shelfList.append(Box(box["location"], box["shelf"]))
        storage.append(shelfList)
    return storage