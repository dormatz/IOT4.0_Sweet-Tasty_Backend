import random
from copy import deepcopy
import torch
import pandas as pd
from Env import Env, Warehouse, Box
from WarehouseMapping import WarehouseMapping, Place
from TSP import TSPsolver
from typing import List, Dict, Tuple, Optional
import json
import pickle
from copy import deepcopy
import math

max_itr = 10

def rewardCalc(storage, inserted_box):
    # get days that the Box was removed and boxes that were remove with it.
    # create groups of items that were removed with the Box in couple of different days.
    # preform TSP on all those group and pick the fastest.
    # return the -1*best_time as the reward.

    box = inserted_box['box']
    id = box.id
    insertedPlace = inserted_box['place']
    outputDF = pd.read_pickle("./outputDF.pkl")
    batches = []  # list of lists of Boxes
    k = 2
    removeDB = deepcopy(outputDF.values)
    n = len(removeDB)
    found = 0
    limit_found = 5
    for i, row in enumerate(outputDF.values):
        if row[2] == id:
            found += 1
            new_batch = []
            for row in removeDB[max(i-k, 0):min(i+k, n)]:
                if row[2] == id:
                    continue
                new_batch.append(Box(row[2], -1*row[1]))
            batches.append(new_batch)
            if (found >= limit_found):
                break
    best_time = math.inf
    for batch in batches:
        cur_time = rewardBatchCalc(batch, storage, insertedPlace)
        if best_time > cur_time:
            best_time = cur_time

    return -1*best_time

def rewardBatchCalc(batch: List[Box], storage, insertedPlace: Place):
    boxesForEachId = []
    itemNotFound = []
    for item in batch:
        boxes = [[Place(box['place'].location, box['place'].shelf)] for box in storage if box['box'].id == item.id and box['box'].quantity >= item.quantity \
                            and not box['place']==insertedPlace]
        if len(boxes) > 3:
            boxes = random.choices(boxes, k=3)
        if len(boxes):
            boxesForEachId.append({'itemId':item.id, 'boxes':boxes})
        else:
            itemNotFound.append(item)
    for item in itemNotFound:
        batch.remove(item)
    if len(boxesForEachId) == 0:
        return TSPsolver([insertedPlace])[1]
    boxesOptions = boxesForEachId[0]['boxes']
    if len(boxesForEachId) > 1:
        for item in boxesForEachId[1:]:
            boxesOptionsWithItem = []
            for option in boxesOptions:
                for place in item['boxes']:
                    if place[0] not in option:
                        #could happen when we want to check two boxes with same id
                        boxesOptionsWithItem.append(option+[place[0]])
            boxesOptions = boxesOptionsWithItem
    for option in boxesOptions:
        option.append(insertedPlace)
    chosenOption = min(deepcopy(boxesOptions), key=lambda obj: TSPsolver(deepcopy(obj))[1])
    return TSPsolver(chosenOption)[1]

class Agent(object):
    def __init__(self, BoxesToInsert: List[Box], warehouse: Warehouse):
        self.env = Env(deepcopy(BoxesToInsert), warehouse)
        self.total_reward = 0

    def step(self):
        actions_probs = torch.nn.functional.softmax(torch.rand(len(self.env.actions)), dim=0)
        action_index = torch.multinomial(actions_probs, 1).item()
        action = self.env.actions[action_index]
        self.env.step(action)
        inserted_box = self.env.state.insertedBoxes[-1]
        #dict of 'place' and 'box'
        storage = deepcopy(self.env.state.warehouse.storage)
        self.total_reward += rewardCalc(storage, inserted_box)

    def fullSteps(self):
        while not self.env.state.isDone():
            self.step()
        return self.env, self.env.state, self.total_reward


def getBestState(BoxesToInsert: List[Box], warehouse=None):
    agent = Agent(BoxesToInsert, deepcopy(warehouse))
    best_env, best_state, best_reward = agent.fullSteps()
    not_changed = 0
    while True:
        agent = Agent(BoxesToInsert, deepcopy(warehouse))
        curr_env, curr_state, curr_reward = agent.fullSteps()
        if curr_reward > best_reward:
            best_reward = curr_reward
            best_state = curr_state
            best_env = curr_env
        else:
            not_changed +=1
        if not_changed == max_itr:
            return best_env, best_state, best_reward


def getRemovedPlaces(itemsToRemove: List[Box], warehouse=None):
    warehouse = Warehouse(0) if warehouse is None else warehouse
    boxesForEachId = []
    itemNotFound = []
    for item in itemsToRemove:
        boxes = [[Place(box['place'].location, box['place'].shelf)] for box in warehouse.storage if box['box'].id == item.id and box['box'].quantity >= item.quantity]
        if len(boxes) > 3:
            boxes = random.choices(boxes, k=3)
        if len(boxes):
            boxesForEachId.append({'itemId':item.id, 'boxes':boxes})
        else:
            itemNotFound.append(item)
    for item in itemNotFound:
        itemsToRemove.remove(item)
    if len(boxesForEachId) == 0:
        return None
    boxesOptions = boxesForEachId[0]['boxes']
    if len(boxesForEachId) > 1:
        for item in boxesForEachId[1:]:
            boxesOptionsWithItem = []
            for option in boxesOptions:
                for place in item['boxes']:
                    if place[0] not in option:
                        #could happen when we want to remove two boxes with same id
                        boxesOptionsWithItem.append(option+[place[0]])
            boxesOptions = boxesOptionsWithItem
    chosenOption = min(deepcopy(boxesOptions), key=lambda obj: TSPsolver(deepcopy(obj))[1])
    for i in range(len(chosenOption)):
        warehouse.removeProducts(chosenOption[i], itemsToRemove[i].quantity)
    return chosenOption, warehouse.addToEmptySpaces, warehouse.updatedStorage
