import config
import telebot
import logging
import datetime
from telebot import types
from pymongo import MongoClient
import pymongo
import pdb
from pprint import pprint
import utils
import doc
bot = telebot.TeleBot(config.token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
client = MongoClient(
    'mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')
db = client.medkzbot_db
patients = db.patients
nurses = db.nurses

patient_buttons = ['Информация про пациента',
                   "Карта пациента", "Помощь", "Часто задаваемые вопросы"]
nurse_buttons = ['Пациенты', "Мой профиль", "Помощь"]
clinics = ['1', '2', '3', '4', '5']
select_user_dict = {}
months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
          'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']


class SelectUser:
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.graft_id = None
        self.date_id = None
        self.status = None


def list_grafts(platform_id):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    grafts = utils.illnesses
    keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data='g' + str(id))
                   for id, name in utils.illness_dict.items()])
    keyboard.add(types.InlineKeyboardButton(
        text='Назад', callback_data='back'))

    return keyboard


def list_dates(platform_id, graft_id):
    keyboard = types.InlineKeyboardMarkup()
    dates = utils.illnesses[graft_id]['dates']

    for i in range(len(dates)):
        keyboard.add(types.InlineKeyboardButton(
            text=dates[i]['date'], callback_data='d'+str(graft_id)+str(i)))

    keyboard.add(types.InlineKeyboardButton(
        text='Назад', callback_data='back'))
    return keyboard


def show_graft_details(patient_id, graft_id, date_id):
    cursor = patients.find_one({'patient_id': patient_id})[
        'grafts'][graft_id]['dates'][date_id]
    return cursor


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if call.message:
        if len(call.data) == 7 and call.data.isdigit():
            user_id = int(call.data)
            user = SelectUser(user_id)
            select_user_dict[chat_id] = user
            keyboard = list_grafts(user_id)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, text="Болезни", reply_markup=keyboard)
        elif call.data[0] == 'g':
            graft_id = int(call.data[1])
            user = select_user_dict[chat_id]
            user.graft_id = graft_id
            keyboard = list_dates(user.patient_id, graft_id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="{0}. Даты получения прививок.".format(
                utils.illnesses[graft_id]['graft_name']), reply_markup=keyboard)
        elif call.data[0] == 'd':
            graft_id = int(call.data[1])
            date_id = int(call.data[2])
            user = select_user_dict[chat_id]
            user.graft_id = graft_id
            user.date_id = date_id
            dic = show_graft_details(user.patient_id, graft_id, date_id)

            if dic['status'] == 0:
                status = 'Ожидается'
            elif dic['status'] == 1:
                status = 'Получил'
            elif dic['status'] == 2:
                status = 'Не получил'
            a = 'Название прививки: {0}\nСрок: {1} дней\nСтатус: {2}'.format(
                utils.illnesses[graft_id]['graft_name'], utils.illnesses[graft_id]['dates'][date_id]['date'], status)
            keyboard = types.InlineKeyboardMarkup()
            bt1 = types.InlineKeyboardButton(
                text="Получил", callback_data='taken')
            bt2 = types.InlineKeyboardButton(
                text="Не получил", callback_data='not taken')
            keyboard.add(bt1, bt2)
            msg = bot.edit_message_text(
                chat_id=chat_id, message_id=call.message.message_id, text=a, reply_markup=keyboard)

        elif call.data == 'taken' or call.data == 'not taken':
            user = select_user_dict[chat_id]
            if call.data == 'taken':
                user.status = 1
            elif call.data == 'not taken':
                user.status = 2
            a = user.graft_id
            b = user.date_id
            setter = {}
            setter['grafts.' + str(a) + '.dates.' +
                   str(b) + '.status'] = user.status
            setter['grafts.' + str(a) + '.dates.' + str(b) +
                   '.updated_at'] = datetime.datetime.utcnow().strftime("%d/%m/%y")
            d = patients.update_one(
                {'patient_id': user.patient_id}, {'$set': setter})
            msg = bot.send_message(chat_id, 'Статус усешно изменен на "{0}"'.format(
                'Получил' if user.status == 1 else 'Не получил'), reply_markup=create_keyboard(nurse_buttons, False, False))
            bot.register_next_step_handler(msg, handle_nurse_menu_buttons)


def change_graft_status(message):
    status_name = message.text
    chat_id = message.chat.id
    user = select_user_dict[chat_id]
    if status_name == 'Получил':
        user.status = 1
    elif status_name == 'Не получил':
        user.status = 2
    patients.update_one({'patient_id': user.patient_id}, {
                        '$set': {'status': user.status}})

    msg = bot.send_message(chat_id, 'Статус усешно изменен',
                           reply_markup=create_keyboard(nurse_buttons, False, False))
    bot.register_next_step_handler(msg, handle_nurse_menu_buttons)


def create_keyboard(words, isOneTime, isContact):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=isOneTime)
    for word in words:
        keyboard.add(types.KeyboardButton(
            text=word, request_contact=isContact))
    return keyboard


def create_inline_keyboard(words, callback_datas):

    patients = dict(zip(callback_datas, words))
    kb = types.InlineKeyboardMarkup()
    for key in patients:
        kb.add(types.InlineKeyboardButton(
            text=patients[key], callback_data=key))

    return kb


def isRegistered(telegram_id):
    a = patients.find({'telegram_id': telegram_id}).count()
    b = nurses.find({'telegram_id': telegram_id}).count()
    if a >= 1:
        return 1
    if b >= 1:
        return 2
    if a == 0 or b == 0:
        return 0


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    res = isRegistered(chat_id)
    if res == 0:
        buttons = ['Зарегистрироваться как медсестра',
                   "Зарегистрироваться как пациент"]
        msg = bot.send_message(chat_id, "Здравствуйте, это телеграм бот платформы 'ЦЕНТР КОНТРОЛЯ COVID-19'. Выберите в качестве кого вы хотите зарегестрироваться.",
                               reply_markup=create_keyboard(buttons, True, False))
        bot.register_next_step_handler(msg, choose_register_type)
    elif res == 1:
        msg = bot.send_message(chat_id, "Добро пожаловать, пациент",
                               reply_markup=create_keyboard(patient_buttons, False, False))
        bot.register_next_step_handler(msg, handle_menu_buttons)
    elif res == 2:
        msg = bot.send_message(chat_id, "Добро пожаловать, медсестра",
                               reply_markup=create_keyboard(nurse_buttons, False, False))
        bot.register_next_step_handler(msg, handle_nurse_menu_buttons)


def handle_menu_buttons(message):
    try:
        chat_id = message.chat.id
        choice = message.text
        if choice == "Помощь":
            msg = bot.send_message(chat_id, "Ok, Помощь")
            bot.register_next_step_handler(msg, handle_menu_buttons)
        elif choice == "Карта пациента":
            send_doc(message)
        elif choice == "Информация про пациента":
            patient_info(message)
        elif choice == "Часто задаваемые вопросы":
            msg = bot.send_message(chat_id, "Ok, Часто задаваемые вопросы")
            bot.register_next_step_handler(msg, handle_menu_buttons)
    except Exception as e:
        bot.reply_to(message, 'oooops')

@bot.message_handler(func=lambda mess: mess.text == "Информация про пациента",
                     content_types=["text"])
def patient_info(message):
    chat_id = message.chat.id
    a = patients.find_one({'telegram_id': chat_id})
    patient_info = 'ФИО: {0} {1} {2}\nДата рождения: {3}/{4}/{5}\nУчасток: {6}\nНомер телефона: {7}'.format(
        a['last_name'], a['first_name'], a['patronymic'], a['day'], a['month'], a['age'], a['clinic'], a['phone_number'])
    msg = bot.send_message(chat_id, patient_info, reply_markup=create_keyboard(
        patient_buttons, False, False))
    bot.register_next_step_handler(msg, handle_menu_buttons)

@bot.message_handler(func=lambda mess: mess.text == "Карта пациента",
                     content_types=["text"])
def send_doc(message):
    chat_id = message.chat.id
    patient = patients.find_one({'telegram_id': chat_id})
    doc.generate_doc(message.chat.id)
    pdffile = open('{0}. Форма 063.pdf'.format(patient['last_name']), 'rb')
    msg = bot.send_document(chat_id, pdffile, reply_markup=create_keyboard(
        patient_buttons, False, False))
    bot.register_next_step_handler(msg, handle_menu_buttons)


def handle_nurse_menu_buttons(message):
    # try:
    chat_id = message.chat.id
    choice = message.text
    if choice == "Помощь":
        msg = bot.send_message(chat_id, "Ok, помощь", reply_markup=create_keyboard(
            nurse_buttons, False, False))
        bot.register_next_step_handler(msg, handle_nurse_menu_buttons)
    elif choice == "Мой профиль":
        cursor = nurses.find_one({'telegram_id': chat_id})
        a = ('Ваш профиль\n'
             'ФИО: '+cursor['last_name']+' '+cursor['first_name'] +
             ' ' + cursor['patronymic'] + '\n'
             'Вы привязаны к ' + str(cursor['clinic'])+' участку' + '\n'
             'Номер телефона: ' + str(cursor['phone_number']))
        msg = bot.send_message(
            chat_id, a, reply_markup=create_keyboard(nurse_buttons, False, False))
        bot.register_next_step_handler(msg, handle_nurse_menu_buttons)

    elif choice == "Пациенты":
        nurse_clinic = int(nurses.find_one({'telegram_id': chat_id})['clinic'])
        p = patients.find({'clinic': nurse_clinic})
        a = ""
        count = p.count()
        if count == 0:
            msg = bot.send_message(chat_id, 'У вас нету пациентов', reply_markup=create_keyboard(
                nurse_buttons, False, False))
        else:
            my_patients = []
            for i in range(count):
                my_patients.append('ФИО: {0} {1} {2}'.format(
                    p[i]['last_name'], p[i]['first_name'], p[i]['patronymic']))
            callbacks = []
            for i in range(count):
                callbacks.append(p[i]['patient_id'])
            msg = bot.send_message(
                chat_id, 'Ваши пациенты', reply_markup=create_inline_keyboard(my_patients, callbacks))
        bot.register_next_step_handler(msg, handle_nurse_menu_buttons)
    # except Exception as e:
    #     bot.reply_to(message, 'oooops')


def choose_register_type(message):
    try:
        chat_id = message.chat.id
        if message.text == 'Зарегистрироваться как медсестра':
            msg = bot.send_message(
                chat_id, "Хорошо! Подготовка к регистрации медсестры")
            msg = bot.reply_to(message, "Ваше имя?")
            bot.register_next_step_handler(msg, process_nurse_first_name_step)
        else:
            msg = bot.send_message(
                chat_id, "Хорошо! Подготовка к регистрации пациента")
            msg = bot.reply_to(message, "Ваше имя?")
            bot.register_next_step_handler(msg, process_first_name_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


# ================================================================================================
# ========================================USER====================================================
# ================================================================================================
user_dict = {}
seqs = db.seqs
seqs.insert({
    'collection': 'patients',
    'id': 0
})


def insert_doc(doc):
    doc['_id'] = str(db.seqs.find_and_modify(
        query={'collection': 'patients'},
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
        self.day = None
        self.month = None
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
        msg = bot.reply_to(message, 'Введите ваш день рождения. Например, 13')
        bot.register_next_step_handler(msg, process_day_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_day_step(message):
    try:
        chat_id = message.chat.id
        day = message.text
        if day.isdigit():
            if not (1 < int(day) < 31):
                msg = bot.reply_to(
                    message, 'Число должно быть в промежутке от 1 до 31')
                bot.register_next_step_handler(msg, process_day_step)
                return
        else:
            msg = bot.reply_to(
                message, 'День должен быть числом. Введите заново')
            bot.register_next_step_handler(msg, process_day_step)
            return
        user = user_dict[chat_id]
        user.day = int(day)
        msg = bot.reply_to(message, 'В каком месяце вы родились?',
                           reply_markup=create_keyboard(months, True, False))
        bot.register_next_step_handler(msg, process_month_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_month_step(message):
    # try:
    chat_id = message.chat.id
    month = message.text
    user = user_dict[chat_id]
    flag = False
    for i in range(0, 11):
        if month == months[i]:
            month = i + 1
            flag = True
    if flag == False:
        msg = bot.reply_to(message, 'Ещё раз выберите месяц')
        bot.register_next_step_handler(msg, process_month_step)
        return
    user.month = int(month)
    msg = bot.reply_to(message, 'В каком году вы родились?')
    bot.register_next_step_handler(msg, process_age_step)
    # except Exception as e:
    #     bot.reply_to(message, 'oooops')


def process_age_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        if age.isdigit():
            if not (1900 < int(age) < 2050):
                msg = bot.reply_to(
                    message, 'Число должно быть в промежутке от 1900 до 2050')
                bot.register_next_step_handler(msg, process_age_step)
                return
        else:
            msg = bot.reply_to(
                message, 'Год должен быть числом. Введите заново')
            bot.register_next_step_handler(msg, process_age_step)
            return
        user = user_dict[chat_id]
        user.age = int(age)
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?',
                           reply_markup=create_keyboard(clinics, False, False))
        bot.register_next_step_handler(msg, process_clinic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_clinic_step(message):
    try:
        chat_id = message.chat.id
        clinic = message.text
        user = user_dict[chat_id]
        if clinic.isdigit():
            user.clinic = int(clinic)
        else:
            raise Exception()

        buttons = ['Отправить мои контакты']
        msg = bot.reply_to(message, 'Отправьте ваши контактные данные',
                           reply_markup=create_keyboard(buttons, False, True))
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
        bot.send_message(chat_id, 'Приятно познакомиться, '+user.last_name+' '+user.first_name+' '+user.patronymic + '\n'
                                  'Дата вашего рождения: ' +
                         str(user.day)+'/'+str(user.month) +
                         '/'+str(user.age) + '\n'
                         'Вы привязаны к ' +
                         str(user.clinic)+' участку' + '\n'
                         'Номер телефона: ' + str(user.phone_number))
        options = ['Да', 'Нет']
        msg = bot.send_message(chat_id, 'Вы уверены что хотите зарегистрироваться?',
                               reply_markup=create_keyboard(options, False, False))
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
                'day': user.day,
                'month': user.month,
                'age': user.age,
                'clinic': user.clinic,
                'phone_number': user.phone_number,
                'registration_date': datetime.datetime.now(),
                'grafts': utils.illnesses
            }
            doc_id = insert_doc(doc)
            year = datetime.datetime.now().year
            patient_id = '{0}{1}{2}'.format(user.clinic, year, doc_id)

            patients.update(
                {'telegram_id': message.chat.id},
                {
                    '$set':
                    {
                        'patient_id': int(patient_id)
                    }
                }
            )
            msg = bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию пациента. Ваш ID: {}".format(
                patient_id), reply_markup=create_keyboard(patient_buttons, False, False))

            bot.register_next_step_handler(msg, handle_menu_buttons)
    except Exception as e:
        bot.reply_to(message, 'oooops')

# =====================================================================================
# ========================================NURSE========================================
# =====================================================================================


nurse_dict = {}
nurse_seqs = db.nurse_seqs
nurse_seqs.insert({
    'collection': 'nurses',
    'id': 0
})


def insert_nurse_doc(doc):
    doc['_id'] = str(db.nurse_seqs.find_and_modify(
        query={'collection': 'nurses'},
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
        msg = bot.reply_to(message, 'К какому участку вы прикреплены?',
                           reply_markup=create_keyboard(clinics, False, False))
        bot.register_next_step_handler(msg, process_nurse_clinic_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_nurse_clinic_step(message):
    try:
        chat_id = message.chat.id
        clinic = message.text
        nurse = nurse_dict[chat_id]
        if clinic.isdigit():
            nurse.clinic = int(clinic)
        else:
            raise Exception()

        buttons = ['Отправить мои контакты']
        msg = bot.reply_to(message, 'Отправьте ваши контактные данные',
                           reply_markup=create_keyboard(buttons, False, True))
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
        bot.send_message(chat_id, 'Приятно познакомиться, '+nurse.last_name+' '+nurse.first_name+' '+nurse.patronymic + '\n'
                         'Вы из ' + str(nurse.clinic)+' участка' + '\n'
                         'Телефонный номер: ' + str(nurse.phone_number))
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        options = ['Да', 'Нет']
        msg = bot.send_message(chat_id, 'Вы уверены что хотите зарегистрироваться?',
                               reply_markup=create_keyboard(options, False, False))
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
                'telegram_id': chat_id,
                'clinic': nurse.clinic,
                'phone_number': nurse.phone_number,
                'registration_date': datetime.datetime.now()
            }
            doc_id = insert_nurse_doc(doc)

            year = datetime.datetime.now().year
            nurse_id = '{0}{1}{2}'.format(nurse.clinic, year, doc_id)

            nurses.update(
                {'telegram_id': message.chat.id},
                {
                    '$set':
                    {
                        'nurse_id': int(nurse_id)
                    }
                }
            )
            msg = bot.send_message(chat_id, "Отлично! Вы успешно прошли регистрацию. Ваш ID: {}".format(
                nurse_id), reply_markup=create_keyboard(nurse_buttons, False, False))

            bot.register_next_step_handler(msg, handle_nurse_menu_buttons)

    except Exception as e:
        bot.reply_to(message, 'oooops')


bot.polling(none_stop=False, interval=0, timeout=20)
