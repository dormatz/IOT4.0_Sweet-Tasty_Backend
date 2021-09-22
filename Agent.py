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
import config

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
    k = 1  # batches of size 3
    removeDB = deepcopy(outputDF.values)
    n = len(removeDB)
    found = 0
    limit_found = 5
    for i, row in enumerate(outputDF.values[1:]):
        if row[2] == id :
            found += 1
            new_batch = []
            for row in removeDB[max(i-k, 0):min(i+k+1, n)]:
                if row[2] == id:
                    continue
                new_batch.append(Box(row[2], -1*row[1]))
            batches.append(new_batch)
            if (found >= limit_found):
                break
    total_time = 0
    #print(f"num of batches found: {len(batches)}")
    for batch in batches:
        #print(len(batch), end="")
        total_time += rewardBatchCalc(batch, storage, insertedPlace)
    mean_time = total_time/len(batches)
    return -1*mean_time

def rewardBatchCalc(batch: List[Box], storage, insertedPlace: Place):
    boxesForEachId = []
    itemNotFound = []
    for item in batch:
        boxes = [[Place(box['place'].location, box['place'].shelf)] for box in storage if box['box'].id == item.id and box['box'].quantity >= item.quantity \
                            and not box['place'] == insertedPlace]

        boxes = boxes[:3]

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
    def __init__(self, BoxesToInsert: List[Box], warehouse: Warehouse, best_total_reward_found_so_far=-math.inf):
        self.env = Env(deepcopy(BoxesToInsert), warehouse)
        self.total_reward = 0
        self.best_total_reward_found_so_far = best_total_reward_found_so_far

    def step(self):
        actions_probs = torch.nn.functional.softmax(torch.rand(len(self.env.actions)), dim=0)
        action_index = torch.multinomial(actions_probs, 1).item()
        action = self.env.actions[action_index]
        self.env.step(action)
        inserted_box = self.env.state.insertedBoxes[-1]  # dict of 'place', 'box' and 'distance'
        storage = deepcopy(self.env.state.warehouse.storage)
        self.total_reward += rewardCalc(storage, inserted_box)

    def findFiniteHorizon(self):
        while (not self.env.state.isDone() and not self.total_reward < self.best_total_reward_found_so_far):
            self.step()
        return self.env, self.env.state, self.total_reward


def getBestState(BoxesToInsert: List[Box], warehouse=None):
    n = len(BoxesToInsert)
    max_itr = min(config.MAX_ITR, choose(config.EMPTY_SPACE_LEN_FACTOR * n, n)+2)
    #print(f"max itr is {max_itr}")
    best_reward = -math.inf
    num_of_horizons_not_improved = 0
    while True:
        agent = Agent(BoxesToInsert, deepcopy(warehouse), best_reward)
        curr_env, curr_state, curr_reward = agent.findFiniteHorizon()
        #print(curr_reward)
        #print('****' + str(num_of_horizons_not_improved))
        if curr_reward > best_reward * (1 - config.EPSILON):
            best_reward = curr_reward
            best_state = curr_state
            best_env = curr_env
            num_of_horizons_not_improved = 0
        else:
            num_of_horizons_not_improved += 1
        if num_of_horizons_not_improved == max_itr:
            return best_env, best_state, best_reward


def getRemovedPlaces(itemsToRemove: List[Box], warehouse=None):
    """Basically choosing which items to remove if there are a lot options with those IDs"""
    warehouse = Warehouse(0) if warehouse is None else warehouse
    boxesForEachId = []
    itemNotFound = []
    for item in itemsToRemove:
        boxes = [[Place(box['place'].location, box['place'].shelf)] for box in warehouse.storage if box['box'].id == item.id and box['box'].quantity >= item.quantity]
        boxes = boxes[:3]
        if len(boxes):
            boxesForEachId.append({'itemId':item.id, 'boxes':boxes})
        else:
            itemNotFound.append(item)
    print(f"found {len(itemsToRemove)-len(itemNotFound)} out of {len(itemsToRemove)}")
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

def choose(n, k):
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in range(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0