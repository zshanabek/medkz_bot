from pymongo import MongoClient
from bson.objectid import ObjectId
from pprint import pprint
import datetime
import random
from random import randrange
from faker import Faker
import utils
client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')

db = client.medkzbot_db
patients = db.patients
nurses = db.nurses

telegram_ids = [155703376,208460287,452755085]
db.patients.delete_many({})
db.nurses.delete_many({})
fake = Faker('ru_RU')
for i in range(20):
    nurses.insert({'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'patronymic': fake.middle_name(),
                'position': fake.job(),
                'telegram_id': 155713374,
                'clinic': random.randint(1, 5),
                'phone_number': fake.phone_number(),
                'nurse_id':random.randint(1000000, 9999999)
                })
    patients.insert({'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'patronymic': fake.middle_name(),
                'telegram_id': 155713374,
                'age': fake.year(),
                'clinic': random.randint(1, 5),
                'phone_number': fake.phone_number(),
                'patient_id':random.randint(1000000, 9999999),
                'grafts':utils.illnesses
                })

a = 0
setter = {}
setter['grafts.'+ str(a) +'.status'] = 1

patients.update_one({'patient_id': 101681584},{'$set':setter})

cursor = patients.find_one({'patient_id':101681584})['grafts']
# cursor = nurses.find({})
# cursor.data.insert({'name':'something'})
# for i in cursor:
pprint(cursor)

# print(cursor.count())
