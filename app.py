from flask import Flask
from flask_restful import reqparse
from Env import Box, saveEmptySpaces, saveStorage, Warehouse
from Agent import getBestState, getRemovedPlaces
from firebase_con import setEmptySpaces
from WarehouseMapping import WarehouseMapping
from TSP import TSPsolver
from copy import deepcopy
import json

app = Flask(__name__)
#app.run(host="0.0.0.0")

@app.route('/insert', methods=['POST', 'GET'])
def insert():
    #SetEmptySpaces() #ONLY WHEN WE WANT TO RESTART THE WAREHOUSE
    parser = reqparse.RequestParser()
    parser.add_argument('ids', type=int, action="append")
    parser.add_argument('quantity', type=int, action="append")
    args = parser.parse_args()
    ids = args['ids']
    quantities = args['quantity']
    boxesToInsert = []
    if args['ids'] is None or len(ids) == 0: return ""
    for i in range(len(ids)):
        boxesToInsert.insert(0, Box(ids[i], quantities[i]))
    best_env, _, _ = getBestState(boxesToInsert)
    filledPlaces = best_env.getFilledPlaces()
    filledBoxes = best_env.getFilledBoxes()
    saveStorage(filledBoxes)
    saveEmptySpaces(filledPlaces)
    tspPlaces, _ = TSPsolver(deepcopy(filledPlaces))
    pri = '{'
    for i, box in enumerate(filledBoxes):
        index = tspPlaces.index(filledPlaces[i])
        pri += f"\"{i}\":[{box['place'].location}, {box['place'].shelf}, {index}],"
    pri = pri[:-1]  # remove the last ,
    pri += '}'
    return pri


@app.route('/remove', methods=['POST', 'GET'])
def remove():
    parser = reqparse.RequestParser()
    parser.add_argument('ids', type=int, action="append")
    parser.add_argument('quantity', type=int, action="append")
    args = parser.parse_args()
    ids = args['ids']
    quantities = args['quantity']
    boxesToRemove = []
    if args['ids'] is None or len(ids) == 0: return ""
    for i in range(len(ids)):
        boxesToRemove.insert(0, Box(ids[i], quantities[i]))
    removedPlaces = getRemovedPlaces(boxesToRemove)
    if removedPlaces is None:
        return "None exist"
    places, emptySpaces, RemovedStorage = removedPlaces
    saveStorage(RemovedStorage)
    saveEmptySpaces(emptySpaces, remove=False)
    tspPlaces, _ = TSPsolver(deepcopy(places))
    print(tspPlaces)
    print(places)
    pri = '{'
    for i, place in enumerate(tspPlaces):
        indexInPlaces = places.index(place)  # bug in here! when the loc is 300 the place in not in the places list. (300,1) is neither in storage nor in emptySpaces
        pri += f"\"{i}\":"+"{"+f"\"id\":{ids[indexInPlaces]}, \"q\":{quantities[indexInPlaces]}, \"location\":{place.location}, \"shelf\":{place.shelf}"+"},"
    pri = pri[:-1]  # remove the last ,
    pri += '}'
    return pri

@app.route('/reset')
def reset():
    setEmptySpaces()
    return 'reset'

@app.route('/clear_all_storage')
def removeAllStorage():
    warehouse = Warehouse(0)
    addToEmptySpaces = [item['place'] for item in warehouse.storage]
    saveEmptySpaces(addToEmptySpaces, remove=False)
    return 'clear_all_storage'

if __name__ == '__main__':
    app.run(debug=True)
