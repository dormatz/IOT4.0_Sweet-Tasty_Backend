from flask import Flask
from flask_restful import reqparse
from Env import Box, saveEmptySpaces, saveStorage
from Agent import getBestState, getRemovedPlaces
from firebase_con import setEmptySpaces
from WarehouseMapping import WarehouseMapping
import json

app = Flask(__name__)

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
    best_env, best_state, best_reward = getBestState(boxesToInsert)
    filledPlaces = best_env.getFiledPlaces()
    filledBoxes = best_env.getFiledBoxes()
    saveStorage(filledBoxes)
    saveEmptySpaces(filledPlaces)
    pri = '{'
    for i, box in enumerate(filledBoxes):
        pri += f"'{i}':[{box['place'].location}, {box['place'].shelf}]"
    pri += '}'
    return pri

@app.route('/remove')
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
    places, emptySpaces, RemovedStorage = getRemovedPlaces(boxesToRemove)
    saveStorage(RemovedStorage)
    saveEmptySpaces(emptySpaces, remove=False)
    wm = WarehouseMapping()
    tspPlaces = wm.TSPsolver(places)
    pri = '{'
    for i, place in enumerate(tspPlaces):
        indexInPlaces = places.index(place)
        pri += f"'{i}':"+"{"+f"'id':{ids[indexInPlaces]}, 'q':{quantities[indexInPlaces]}, \
             'location':{place.location}, 'shelf':{place.shelf}"+"}"
    pri += '}'
    return pri

@app.route('/reset')
def reset():
    setEmptySpaces()
    return 'reset'

if __name__ == '__main__':
    app.run(debug=True)
