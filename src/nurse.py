import config
import telebot
import logging
import datetime
from telebot import types
from pymongo import MongoClient
import pymongo

positions = ['Медсестра 1','Медсестра 2','Медсестра 3','Медсестра 4', 'Медсестра 5']
bot = telebot.TeleBot(config.token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
nurse_dict = {}
client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')
db = client.medkzbot_db
nurses = db.nurses
nurs_seqs = db.nurs_seqs
nurs_seqs.insert({
    'collection' : 'nurses',
    'id' : 0
})


def insert_doc(doc):
    doc['_id'] = str(db.seqs.find_and_modify(
        query={ 'collection' : 'nurses' },
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True 
    ).get('id'))

    return doc['_id']
    try:
        nurses.insert(doc)

    except pymongo.errors.DuplicateKeyError as e:
        insert_doc(doc)


class Nurse:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = None
        self.patronymic = None
        self.position = None
        self.clinic = None

def process_nurse_first_name_step(message):
    try:
        chat_id = message.chat.id
        first_name = message.text
        nurse = Nurse(first_name)
        nurse_dict[chat_id] = nurse
        msg = bot.reply_to(message, 'Ваша фамилия?')
        bot.register_next_step_handler(msg, process_nurse_last_name_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_nurse_last_name_step(message):
    try:
        chat_id = message.chat.id
        last_name = message.text
        nurse = nurse_dict[chat_id]
        nurse.last_name = last_name
        msg = bot.reply_to(message, 'Ваше отчество?')
        bot.register_next_step_handler(msg, process_nurse_patronymic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_nurse_patronymic_step(message):
    try:
        chat_id = message.chat.id
        patronymic = message.text
        nurse = nurse_dict[chat_id]
        nurse.patronymic = patronymic
        msg = bot.reply_to(message, 'Ваша должность?')
        bot.register_next_step_handler(msg, process_nurse_position_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_nurse_position_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        nurse = nurse_dict[chat_id]
        nurse.age = age
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for i in positions:
            markup.add(i)
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_nurse_clinic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_nurse_clinic_step(message):
    try:
        chat_id = message.chat.id
        clinic = message.text
        nurse = nurse_dict[chat_id]
        if clinic.isdigit():
            nurse.clinic = clinic
        else:
            raise Exception()
        bot.send_message(chat_id,'Приятно познакомиться, '+nurse.last_name+' '+nurse.first_name+' '+nurse.patronymic + '\n'
                                 'Ваш год рождения: ' + str(nurse.age) + '\n'
                                 'Вы из '+nurse.clinic+' участка')  
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.send_message(chat_id, 'Вы уверены что хотите зарегистрироваться?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_nurse_confirmation_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')
    
def process_nurse_confirmation_step(message):
    try:
        chat_id = message.chat.id
        confirm = message.text
        nurse = nurse_dict[chat_id]

        if confirm == u'Да':
            doc = {
                'first_name': nurse.first_name,
                'last_name': nurse.last_name,
                'patronymic': nurse.patronymic,
                'position': nurse.position,
                'clinic': nurse.clinic
            }
            doc_id = insert_doc(doc)
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(nurse.clinic, year,doc_id)
            bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(patient_id))


            
    except Exception as e:
        bot.reply_to(message, 'oooops')