from pymongo import MongoClient
from bson.objectid import ObjectId
from pprint import pprint
import datetime
import random
from random import randrange
from faker import Faker

client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')

db = client.medkzbot_db
patients = db.patients

# db.patients.delete_many({})
# patients.insert_one({
#     'first_name': 'Zhunissali',
#     'last_name': 'Shanabek',
#     'patronymic': 'Amiruly',
#     'age': 20,  
#     'clinic': 4,                          
# })

cursor = patients.find()
for document in cursor: 
    pprint(document)