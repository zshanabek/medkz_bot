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

patient_buttons = ['Карта пациента',"Таблица","Диагнозы и лечения", "Помощь", "Часто задаваемые вопросы"]
nurse_buttons = ['Пациенты', "Помощь"]
def create_keyboard(words, isOneTime, isContact):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=isOneTime)
    for word in words:
        keyboard.add(types.KeyboardButton(text=word, request_contact=isContact))
    return keyboard

def isRegistered(telegram_id):
    a = patients.find({'telegram_id': telegram_id}).count()
    b = nurses.find({'telegram_id': telegram_id}).count()
    return 'nurse'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    res = isRegistered(chat_id)
    bot.send_message(chat_id, str(res))
    if res==True:
        buttons = ['Зарегистрироваться как медсестра',"Зарегистрироваться как пациент"]
        msg = bot.send_message(chat_id, "Выберите функцию", reply_markup=create_keyboard(buttons,False,False))
        bot.register_next_step_handler(msg, choose_register_type)
    elif res == 'patient':        
        msg = bot.send_message(chat_id, "Добро пожаловать, пациент", reply_markup=create_keyboard(patient_buttons,False,False))
        bot.register_next_step_handler(msg, handle_menu_buttons)
    elif res == 'nurse':
        msg = bot.send_message(chat_id, "Добро пожаловать, медсестра", reply_markup=create_keyboard(nurse_buttons,False,False))
        bot.register_next_step_handler(msg, handle_nurse_menu_buttons)

def handle_menu_buttons(message):
    chat_id = message.chat.id

    choice = message.text

    if choice == "Карта пациента":
        a = patients.find_one({'telegram_id':message.chat.id})
        patient_info = '''Фамилия: {0}\nИмя: {1}\nОтчество: {2}\nГод рождения: {3}\nУчасток: {4}\n'''.format(a['last_name'], a['first_name'], a['patronymic'], a['age'], a['clinic'])
        msg = bot.send_message(chat_id, patient_info, reply_markup=create_keyboard(patient_buttons, False, False))
        bot.register_next_step_handler(msg, handle_menu_buttons)
    elif choice == "Диагнозы и лечения":
        grafts = patients.find_one({'telegram_id':message.chat.id})['grafts']
        a = ''
        for i in range(len(grafts)):
            a += '{0}. Название прививки: {1}\nСтатус: {2}\n\n'.format(i,grafts[i]['graft_name'],grafts[i]['status'])

        msg = bot.send_message(chat_id, a,reply_markup=create_keyboard(patient_buttons, False, False))
        bot.register_next_step_handler(msg, handle_menu_buttons)
    elif choice == "Помощь":
        bot.send_message(chat_id, "Ok, Помощь")
    elif choice == "Часто задаваемые вопросы":
        bot.send_message(chat_id, "Ok, Часто задаваемые вопросы")

def handle_nurse_menu_buttons(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == "Помощь":
        bot.send_message(chat_id, "Ok, помощь")
    elif choice == "Пациенты":        
        nurse_clinic = nurses.find_one({'telegram_id':message.chat.id})['clinic']
        p = patients.find({'clinic':nurse_clinic})

        a = ""
        for i in range(p.count()):
            a+='ФИО: {0} {1} {2}\nГод рождения: {3}\nУчасток: {4}\n\n'.format(p[i]['last_name'], 
            p[i]['first_name'], p[i]['patronymic'], p[i]['age'], p[i]['clinic'])
        bot.send_message(chat_id, a, reply_markup=create_keyboard(nurse_buttons, False, False))


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

# ================================================================================================
# ========================================USER====================================================
# ================================================================================================
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
        self.phone_number = None
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
        msg = bot.reply_to(message, 'Введите год рождения. Например, 2017')
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_age_step(message):
    # try:
        chat_id = message.chat.id
        age = message.text
        if age.isdigit():
            if not (1900 < int(age) < 2050):
                msg = bot.reply_to(message, 'Число должно быть в промежутке от 1900 до 2050')
                bot.register_next_step_handler(msg, process_age_step)
                return   
        else:
            msg = bot.reply_to(message, 'Год должен быть числом. Введите заново')
            bot.register_next_step_handler(msg, process_age_step)
            return   
        user = user_dict[chat_id]
        user.age = int(age)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('1', '2', '3', '4', '5')
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_clinic_step)
    # except Exception as e:
    #     bot.reply_to(message, 'oooops')

def process_clinic_step(message):
    try:
        chat_id = message.chat.id
        clinic = message.text
        user = user_dict[chat_id]
        if clinic.isdigit():
            user.clinic = clinic
        else:
            raise Exception()
        
        buttons = ['Отправить мои контакты']
        msg = bot.reply_to(message, 'Отправьте ваши контактные данные', reply_markup=create_keyboard(buttons,True,True))
        bot.register_next_step_handler(msg, process_phone_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_phone_step(message):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        if message.contact.phone_number:
            user.phone_number = message.contact.phone_number
        else:
            raise Exception()

        bot.send_message(chat_id,'Приятно познакомиться, '+user.last_name+' '+user.first_name+' '+user.patronymic + '\n'
                                 'Ваш год рождения: ' + str(user.age) + '\n'
                                 'Вы привязаны к '+user.clinic+' участку'+ '\n'
                                 'Номер телефона: ' + str(user.phone_number))  
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
                'clinic': user.clinic,
                'phone_number': user.phone_number
            }
            doc_id = insert_doc(doc)
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(user.clinic, year,doc_id)
            bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(patient_id))
    except Exception as e:
        bot.reply_to(message, 'oooops')

# =====================================================================================
# ========================================NURSE========================================
# =====================================================================================


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
        self.phone_number = None
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
        
        buttons = ['Отправить мои контакты']
        msg = bot.reply_to(message, 'Отправьте ваши контактные данные', reply_markup=create_keyboard(buttons,True,True))
        bot.register_next_step_handler(msg, process_nurse_phone_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_nurse_phone_step(message):
    try:
        chat_id = message.chat.id
        nurse = nurse_dict[chat_id]
        if message.contact.phone_number:
            nurse.phone_number = message.contact.phone_number
        else:
            raise Exception()
        bot.send_message(chat_id,'Приятно познакомиться, '+nurse.last_name+' '+nurse.first_name+' '+nurse.patronymic + '\n'
                                 'Ваша должность: ' + str(nurse.position) + '\n'
                                 'Вы из '+nurse.clinic+' участка'+ '\n'
                                 'Телефонный номер: ' + str(nurse.phone_number))  
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
                'clinic': nurse.clinic,
                'phone_number': nurse.phone_number
            }
            doc_id = insert_nurse_doc(doc)
        
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(nurse.clinic, year,doc_id)
            bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(patient_id))


            
    # except Exception as e:
    #     bot.reply_to(message, 'oooops')
bot.polling()
