import random
from copy import deepcopy
import torch
from Env import Env, Warehouse, Box
from WarehouseMapping import WarehouseMapping, Place
from TSP import TSPsolver
from typing import List, Dict, Tuple, Optional
import json

max_itr = 10

def rewardCalc(storage: List[Dict[Place, Box]], inserted_box: Dict[Place, Box]):
    #dict of 'place' and 'box'
    return 1

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
    agent = Agent(BoxesToInsert, warehouse)
    best_env, best_state, best_reward = agent.fullSteps()
    not_changed = 0
    while True:
        agent = Agent(BoxesToInsert, warehouse)
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
