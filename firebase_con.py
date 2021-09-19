import firebase_admin
from firebase_admin import credentials, firestore
from WarehouseMapping import Place, SHELFS, LOCATIONS_PER_AISLE, AISLES, WarehouseMapping
from Env import Place
import os

def connect():
    if not firebase_admin._apps:
        fb_admin = os.path.join(os.path.join(os.getcwd(), 'firebase'), 'sweet-and-testy-firebase-adminsdk-p9msu-bb41457a7f.json')
        cred = credentials.Certificate(fb_admin)
        firebase_admin.initialize_app(cred, {'projectId': 'sweet-and-testy'})
    return firestore.client()

def setEmptySpaces():
    #RESTART EMPTY SPACES!#
    db = connect()
    coll = db.collection('emptySpaces')
    wm = WarehouseMapping()
    emptySpaces = [{'location':location, 'shelf':shelf,  'distanceFromEntrance':
                    wm.fromEntrance(Place(location, shelf))} for shelf in range(SHELFS)
                    for location in range(LOCATIONS_PER_AISLE*AISLES)]
    for place in emptySpaces:
        coll.document(f"{place['location']}, {place['shelf']}").set(place)


def getEmptySpaceCollectionFirebase(size):
    db = connect()
    docs = db.collection('emptySpaces').order_by('distanceFromEntrance').limit(size).get()
    return docs

def getStorageCollectionFirebase(ids=None):
    db = connect()
    if ids == None:
        docs = db.collection('storage').get()
    else:
        docs = db.collection('storage').where(u'id', u'in', ids).get()
    return docs

def updateStorageCollectionFirebase(place, box, delete=False):
    db = connect()
    if delete:
        db.collection('storage').document(f'{place.location}, {place.shelf}').delete()
        return
    data = place.__dict__
    data.update(box.__dict__)
    db.collection('storage').document(f'{place.location}, {place.shelf}').set(data)


def updateEmptySpaces(place, delete=False):
    wm = WarehouseMapping()
    db = connect()
    if delete:
        db.collection('emptySpaces').document(f'{place.location}, {place.shelf}').delete()
        return
    data = place.__dict__
    data.update({'distanceFromEntrance':wm.fromEntrance(place)})
    docs = db.collection('emptySpaces').document(f'{place.location}, {place.shelf}').set(data)
