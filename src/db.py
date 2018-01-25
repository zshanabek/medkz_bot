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
nurses = db.nurses

# db.patients.delete_many({})
# db.nurses.delete_many({})

# patients.insert_one({
#     'first_name': 'Zhunissali',
#     'last_name': 'Shanabek',
#     'patronymic': 'Amiruly',
#     'age': 20,  
#     'clinic': 4,                          
# })

# patients.insert_one({
#     'first_name': 'Zhunissali',
#     'last_name': 'Shanabek',
#     'patronymic': 'Amiruly',
#     'age': 20,  
#     'clinic': 4,                          
# })
# print(nurses.find({'telegram_id': 208460287}).count())

patients.update(
    {'telegram_id':452755085},
    {
        '$set':{
            'grafts':[
                {
                    'graft_name':'от ветрянки',
                    'status':'Получил'
                },
                {
                    'graft_name':'от кори',
                    'status':'Не получил'
                }
            ]
        }
    }
)
cursor = patients.find({})
# cursor = nurses.find({})
# cursor.data.insert({'name':'something'})
for document in cursor: 
    pprint(document)