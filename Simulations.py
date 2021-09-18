import pandas as pd
import numpy as np
from Env import Box
import random
from WarehouseMapping import NUM_OF_PLACES
from time import time
from SimulatedWarehouses import GreedyWarehouse, RandomWarehouse
from SmartWarehouseSimulation import SmartWarehouse
import matplotlib.pyplot as plt
from tabulate import tabulate
from pathlib import Path

""" Module to run simulations to prove that we do achieve improvements
 This module doesnt runs as a part of the actual "product" so it can be inefficient"""
class Simulation:
    def __init__(self):
        self.smartWarehouse = SmartWarehouse()
        self.greedyWarehouse = GreedyWarehouse()
        self.randomWarehouse = RandomWarehouse()
        self.smart_insert_times = []
        self.greedy_insert_times = []
        self.random_insert_times = []
        self.smart_remove_times = []
        self.greedy_remove_times = []
        self.random_remove_times = []

    def setup(self):
        df = pd.read_csv(Path('csvs','Warehouse_traffic.csv'))
        df['Quantity'] = df['Quantity'].astype(int)
        inputDF = df.loc[df['Quantity'] > 0]  # 3742. 764 unique
        outputDF = df.loc[df['Quantity'] < 0]  # the rest, something like 80000. 1382 unique


        # the intersection between the output and the output is 722 products_id, which is good.
        relevantIDs = np.intersect1d(np.unique(inputDF['Product_ID'].values),
                       np.unique(outputDF['Product_ID'].values))

        """"Insert setup"""
        # We simulate only with the ID that in the intersection
        self._boxesToInsert = [Box(id,q) for q,id
                         in inputDF[['Quantity', 'Product_ID']].values.astype(int)
                         if id in relevantIDs]

        self._boxesToInsert.reverse()
        # fill random boxes to insert based on random sampling from existing ones so that the number of boxes will fill the warehouse
        k_to_fill = NUM_OF_PLACES-len(relevantIDs)-5
        idChoices = random.choices(relevantIDs, k=NUM_OF_PLACES-len(relevantIDs)-5)
        for i in range(k_to_fill):
            m = random.randint(10, 500)
            j = random.randint(0, len(self._boxesToInsert))
            self._boxesToInsert.insert(j, Box(idChoices[i], m))

        # create the real boxesToInsert which is list of lists. every inner list is a batch for one insertion.
        i = 0
        n = len(self._boxesToInsert)
        self.boxesToInsert = []  # will be list of lists
        while(i<n):
            size = random.randint(3, 7)
            if(i+size > n):
                size = n-i  # so we wont get out of bounds
            self.boxesToInsert.append(self._boxesToInsert[i:i+size])
            i += size

        """"Remove setup"""
        # dropping duplicates of products which happens more than once in the same day
        for i, d in enumerate(outputDF.groupby(by=['Date'])):
            if i == 0:
                resDF = pd.DataFrame(d[1].drop_duplicates('Product_ID'))
            else:
                resDF = resDF.append(d[1].drop_duplicates('Product_ID'))

        outputDF = resDF
        outputDF.to_pickle("./outputDF.pkl")

        self._boxesToRemove = [Box(id, -q) for q, id
                         in outputDF[['Quantity', 'Product_ID']].values.astype(int)
                         if id in relevantIDs]
        self._boxesToRemove.reverse()
        i = 0
        n = len(self._boxesToRemove)
        self.boxesToRemove = []  # will be list of lists
        while (i < n):
            size = random.randint(3, 7)
            if (i + size > n):
                size = n - i  # so we wont get out of bounds
            self.boxesToRemove.append(self._boxesToRemove[i:i + size])
            i += size


        # self.boxesToRemove = random.sample(boxesToRemove, k=len(boxesToRemove))

        # for every product, in how many days it gets removed out of the warehouse (num_of_days)
        oDF = outputDF.drop_duplicates('Product_ID')
        oDF = oDF['Product_ID'].values
        oDF = [i for i in oDF if i in relevantIDs]
        num_of_days = []
        for id in oDF:
            num_of_days.append(len(outputDF.loc[outputDF['Product_ID'] == id].drop_duplicates('Date')))

    def run(self):
        for listOfBoxes in self.boxesToInsert:
            self.smart_insert_times.append(self.smartWarehouse.insertBoxes(listOfBoxes))
            self.greedy_insert_times.append(self.greedyWarehouse.insertBoxes(listOfBoxes))
            self.random_insert_times.append(self.randomWarehouse.insertBoxes(listOfBoxes))

        self.greedyWarehouse.organizeStorageList()
        self.randomWarehouse.organizeStorageList()

        for listOfBoxes in self.boxesToRemove:
            self.smart_remove_times.append(self.smartWarehouse.removeProducts(listOfBoxes))
            self.greedy_remove_times.append(self.greedyWarehouse.removeProducts(listOfBoxes))
            self.random_remove_times.append(self.randomWarehouse.removeProducts(listOfBoxes))

    def showResults(self):
        smart_better_than_greedy = 0
        smart_better_than_random = 0
        n = len(self.boxesToRemove)
        for i in range(n):
            if self.smart_remove_times[i] < self.greedy_remove_times[i]:
                smart_better_than_greedy += 1
            if self.smart_remove_times[i] < self.random_remove_times[i]:
                smart_better_than_random += 1

        print('SmartWarehouse is better than GreedyWarehouse in' +
              str(float(smart_better_than_greedy*100)/float(n)) + 'of the cases')
        print('SmartWarehouse is better than RandomWarehouse in' +
              str(float(smart_better_than_random*100)/float(n)) + 'of the cases')

        total_remove_time_smart = sum(self.smart_remove_times)
        total_insert_time_smart = sum(self.smart_insert_times)
        total_remove_time_greedy = sum(self.greedy_remove_times)
        total_insert_time_greedy = sum(self.greedy_insert_times)
        total_remove_time_random = sum(self.random_remove_times)
        total_insert_time_random = sum(self.random_insert_times)

        print('Total times')
        print(
            tabulate({'Insertion': [total_insert_time_smart, total_insert_time_greedy, total_insert_time_random],
                      'Removal': [total_remove_time_smart,total_remove_time_greedy, total_remove_time_random]},
                     headers='keys', tablefmt='fancy_grid',
                     showindex=['Smart', 'Greedy', 'Random'])
        )


        mean_remove_time_smart = np.mean(self.smart_remove_times)
        mean_insert_time_smart = np.mean(self.smart_insert_times)
        mean_remove_time_greedy = np.mean(self.greedy_remove_times)
        mean_insert_time_greedy = np.mean(self.greedy_insert_times)
        mean_remove_time_random = np.mean(self.random_remove_times)
        mean_insert_time_random = np.mean(self.random_insert_times)

        print('Mean times')
        print(
            tabulate({'Insertion': [mean_insert_time_smart, mean_insert_time_greedy, mean_insert_time_random],
                      'Removal': [mean_remove_time_smart, mean_remove_time_greedy, mean_remove_time_random]},
                     headers='keys', tablefmt='fancy_grid',
                     showindex=['Smart', 'Greedy', 'Random'])
        )

        plt.scatter(range(n), self.smart_insert_times)
        plt.scatter(range(n), self.greedy_insert_times)
        plt.scatter(range(n), self.random_insert_times)
        plt.title('Insertion times')
        plt.show()
        plt.scatter(range(n), self.smart_remove_times)
        plt.scatter(range(n), self.random_remove_times)
        plt.scatter(range(n), self.greedy_remove_times)
        plt.title('Removal times')
        plt.show()

if __name__ == '__main__':
    s= Simulation()
    s.setup()
    x = 0
    print(s.boxesToRemove[0])
