import random
from copy import deepcopy
import torch
from Env import Env, Warehouse, Box
from WarehouseMapping import WarehouseMapping, Place
from TSP import TSPsolver
import json

max_itr = 10

class Agent(object):
    def __init__(self, BoxesToInsert, warehouse):
        self.env = Env(deepcopy(BoxesToInsert), warehouse)
        self.total_reward = 0
        self.policy = {self.env.state: { "actions_probability": torch.nn.functional.softmax(torch.rand(len(self.env.actions)), dim=0) } }

    def step(self):
        if self.env.state not in self.policy:
            self.policy.append({self.env.state: { "actions_probability": torch.nn.functional.softmax(torch.rand(len(self.env.actions)))}})
        actions_probs = self.policy[self.env.state]["actions_probability"]
        action_index = torch.multinomial(actions_probs, 1).item()
        action = self.env.actions[action_index]
        self.env.step(action)
        self.total_reward += self.rewardCalc(action)

    def fullSteps(self):
        while not self.env.state.isDone():
            self.step()
        return self.env, self.env.state, self.total_reward

    def rewardCalc(self, action):
        return 1


def getBestState(BoxesToInsert, warehouse=None):
    agent = Agent(BoxesToInsert, warehouse)
    best_env, best_state, best_reward = agent.fullSteps()
    return best_env, best_state, best_reward
    not_changed = 0
    while True:
        agent = Agent(BoxesToInsert)
        curr_env, curr_state, curr_reward = agent.fullSteps()
        if curr_reward > best_reward:
            best_reward = curr_reward
            best_state = curr_state
            best_env = curr_env
        else: not_changed +=1
        if not_changed == max_itr:
            return best_env, best_state, best_reward


def getRemovedPlaces(itemsToRemove, warehouse=None):
    warehouse = Warehouse(0) if warehouse is None else warehouse
    boxesForEachId = []
    for item in itemsToRemove:
        boxes = [[Place(box['place'].location, box['place'].shelf)] for box in warehouse.storage if box['box'].id == item.id and box['box'].quantity >= item.quantity]
        boxesForEachId.append({'itemId':item.id, 'boxes':boxes})

    boxesOptions = boxesForEachId[0]['boxes']
    for item in boxesForEachId[1:]:
        boxesOptionsWithItem = []
        for option in boxesOptions:
            current_option = deepcopy(option)
            for place in item['boxes']:
                if place[0] not in current_option:
                    #could happen when we want to remove two boxes with same id
                    boxesOptionsWithItem.append(current_option.append(place[0]))
        boxesOptions = boxesOptionsWithItem
    chosenOption = min(boxesOptions, key=lambda obj: TSPsolver(obj))
    for i in range(len(chosenOption)):
        warehouse.removeProducts(chosenOption[i], itemsToRemove[i].quantity)
    return chosenOption, warehouse.addToEmptySpaces, warehouse.updatedStorage

def relevantBox(box: Box, items):
    for item in items:
        if item.id == box.id and item.quantity <= box.quantity:
            return True
