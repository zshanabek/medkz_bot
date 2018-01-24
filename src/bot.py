import config
import telebot
import logging
import datetime
from telebot import types
from pymongo import MongoClient
import pymongo


bot = telebot.TeleBot(config.token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')
db = client.medkzbot_db
patients = db.patients
nurses = db.nurses

def create_keyboard(words, isOneTime, isContact):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=isOneTime)
    for word in words:
        keyboard.add(types.KeyboardButton(text=word, request_contact=isContact))
    return keyboard

def isRegistered(telegram_id):
    a = patients.find({'telegram_id': telegram_id}).count()
    b = nurses.find({'telegram_id': telegram_id}).count()
    if a==1:
        return 1
    elif b==1:
        return 2
    elif a==0 or b==0:
        return True
    else:
        return False
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    res = isRegistered(chat_id)
    if res==True:
        buttons = ['Зарегистрироваться как медсестра',"Зарегистрироваться как пациент"]
        msg = bot.send_message(chat_id, "Выберите функцию", reply_markup=create_keyboard(buttons,True,False))
        bot.register_next_step_handler(msg, choose_register_type)
    elif res == 1:
        msg = bot.send_message(chat_id, "Добро пожаловать пациент")
    elif res == 2:
        msg = bot.send_message(chat_id, "Добро пожаловать медсестра")


def choose_register_type(message):
    chat_id = message.chat.id
    if message.text == 'Зарегистрироваться как медсестра':
        msg = bot.send_message(chat_id, "Хорошо! Подготовка к регистрации медсестры")
        msg = bot.reply_to(message, "Ваше имя?")
        bot.register_next_step_handler(msg, process_nurse_first_name_step)
    else:
        msg = bot.send_message(chat_id, "Хорошо! Подготовка к регистрации пациента")
        msg = bot.reply_to(message, "Ваше имя?")
        bot.register_next_step_handler(msg, process_first_name_step)
# ========================================USER====================================================
user_dict = {}
seqs = db.seqs
seqs.insert({
    'collection' : 'patients',
    'id' : 0
})

def insert_doc(doc):
    doc['_id'] = str(db.seqs.find_and_modify(
        query={ 'collection' : 'patients' },
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True 
    ).get('id'))

    try:
        patients.insert(doc)

    except pymongo.errors.DuplicateKeyError as e:
        insert_doc(doc)
    
    return doc['_id']

class User:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = None
        self.patronymic = None
        self.age = None
        self.clinic = None


@bot.message_handler(commands=['patient'])
def meet_patient(message):
    msg = bot.reply_to(message, "Ваше имя?")
    bot.register_next_step_handler(msg, process_first_name_step)

def process_first_name_step(message):
    try:
        chat_id = message.chat.id
        first_name = message.text
        user = User(first_name)
        user_dict[chat_id] = user
        msg = bot.reply_to(message, 'Ваша фамилия?')
        bot.register_next_step_handler(msg, process_last_name_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_last_name_step(message):
    try:
        chat_id = message.chat.id
        last_name = message.text
        user = user_dict[chat_id]
        user.last_name = last_name
        msg = bot.reply_to(message, 'Ваше отчество?')
        bot.register_next_step_handler(msg, process_patronymic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_patronymic_step(message):
    try:
        chat_id = message.chat.id
        patronymic = message.text
        user = user_dict[chat_id]
        user.patronymic = patronymic
        msg = bot.reply_to(message, 'Год вашего рождения?')
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_age_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        if not age.isdigit():
            msg = bot.reply_to(message, 'Год должен быть числом')
            bot.register_next_step_handler(msg, process_age_step)
            return
        user = user_dict[chat_id]
        user.age = age
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('1', '2', '3', '4', '5')
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_clinic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_contact_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        if not age.isdigit():
            msg = bot.reply_to(message, 'Год должен быть числом')
            bot.register_next_step_handler(msg, process_age_step)
            return
        user = user_dict[chat_id]
        user.age = age
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('1', '2', '3', '4', '5')
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_clinic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_clinic_step(message):
    try:
        chat_id = message.chat.id
        clinic = message.text
        user = user_dict[chat_id]
        if clinic.isdigit():
            user.clinic = clinic
        else:
            raise Exception()
        bot.send_message(chat_id,'Приятно познакомиться, '+user.last_name+' '+user.first_name+' '+user.patronymic + '\n'
                                 'Ваш год рождения: ' + str(user.age) + '\n'
                                 'Вы привязаны к '+user.clinic+' участку')  
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.send_message(chat_id, 'Вы уверены что хотите зарегистрироваться?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_confirmation_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')
    
def process_confirmation_step(message):
    try:
        chat_id = message.chat.id
        confirm = message.text
        user = user_dict[chat_id]

        if confirm == u'Да':
            doc = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'patronymic': user.patronymic,
                'telegram_id': chat_id,
                'age': user.age,
                'clinic': user.clinic
            }
            doc_id = insert_doc(doc)
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(user.clinic, year,doc_id)
            bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(patient_id))


            
    except Exception as e:
        bot.reply_to(message, 'oooops')


# ========================================NURSE========================================
nurse_dict = {}
positions = ['Медсестра 1','Медсестра 2','Медсестра 3','Медсестра 4', 'Медсестра 5']
nurse_seqs = db.nurse_seqs
nurse_seqs.insert({
    'collection' : 'nurses',
    'id' : 0
})


def insert_nurse_doc(doc):
    doc['_id'] = str(db.nurse_seqs.find_and_modify(
        query={ 'collection' : 'nurses' },
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True 
    ).get('id'))

    try:
        nurses.insert(doc)

    except pymongo.errors.DuplicateKeyError as e:
        insert_nurse_doc(doc)

    return doc['_id']

class Nurse:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = None
        self.patronymic = None
        self.position = None
        self.clinic = None

@bot.message_handler(commands=['nurse'])
def meet_nurse(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "Ваше имя?")
    bot.register_next_step_handler(msg, process_nurse_first_name_step)

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
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for i in positions:
            markup.add(i)
        msg = bot.reply_to(message, 'Ваша должность?', reply_markup = markup)
        bot.register_next_step_handler(msg, process_nurse_position_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_nurse_position_step(message):
    try:
        chat_id = message.chat.id
        position = message.text
        nurse = nurse_dict[chat_id]
        nurse.position = position
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('1', '2', '3', '4', '5')
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
                                 'Ваша должность: ' + str(nurse.position) + '\n'
                                 'Вы из '+nurse.clinic+' участка')  
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.send_message(chat_id, 'Вы уверены что хотите зарегистрироваться?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_nurse_confirmation_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')
    
def process_nurse_confirmation_step(message):
    # try:
        chat_id = message.chat.id
        confirm = message.text
        nurse = nurse_dict[chat_id]

        if confirm == u'Да':
            doc = {
                'first_name': nurse.first_name,
                'last_name': nurse.last_name,
                'patronymic': nurse.patronymic,
                'position': nurse.position,
                'telegram_id': chat_id,
                'clinic': nurse.clinic
            }
            doc_id = insert_nurse_doc(doc)
        
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(nurse.clinic, year,doc_id)
            bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(patient_id))


            
    # except Exception as e:
    #     bot.reply_to(message, 'oooops')
bot.polling()
