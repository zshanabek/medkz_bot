from fpdf import FPDF
import src.utils
import pdb
import datetime
from pymongo import MongoClient
client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')

db = client.medkzbot_db
patients = db.patients
patient = patients.find_one({'telegram_id': 483742281})
grafts = patient['grafts']
pdf=FPDF(format='letter', unit='in')
pdf.add_page()

pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
epw = pdf.w - 2*pdf.l_margin
col_width = epw/11
 
data= [['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '', '']]
k = 1
for j in range(0,10):
    data[0][k] = src.utils.illness_names[j]
    k+=1

k = 1
for i in range(0, 10):
    data[k][0] = src.utils.dates[i]
    k+=1

def find_point(i, j):
    for item in grafts:
        if item['graft_id'] == i:
            for dat in item['dates']:
                if dat['date_id'] == j:
                    if dat['status'] == 1:
                        data[j + 1][i + 1] = 'Да' + '\n' + str(dat['updated_at'])
                    else:
                        data[j + 1][i + 1] = 'Нет'     

for i in range(0, 10):
    for j in range(0, 10):
        find_point(i, j)
    
pdf.set_font('DejaVu', '', 14)
pdf.cell(epw, 0.0, 'Карта пациента', align='C')
pdf.ln(0.5)
pdf.cell(epw, 0.0, "ФИО: {0} {1} {2}".format(patient['last_name'], patient['first_name'], patient['patronymic']), align='C')
pdf.ln(0.5)
pdf.set_font('DejaVu', '', 6)
th = pdf.font_size
current_y = pdf.get_y() 
initial = pdf.get_y() 
initial = pdf.get_x()
current_x = pdf.get_x()
for i in range (0, 11):
    for j in range(0, 11):
        if (i == 0 and j == 3):
            pdf.multi_cell(col_width, 0.2, str(data[i][j]), border=1, align = 'C')
        elif (i == 0 and j == 4):
            pdf.multi_cell(col_width, 0.1, str(data[i][j]), border=1, align = 'C')
        elif (i == 0 and j == 5):
            pdf.multi_cell(col_width, 0.2, str(data[i][j]), border=1, align = 'C')
        elif (i == 0 and j == 6):
            pdf.multi_cell(col_width, 0.2, str(data[i][j]), border=1, align = 'C')
        elif (i == 0 and j == 7):
            pdf.multi_cell(col_width, 0.135, str(data[i][j]), border=1, align = 'C')
        else:
            if len(str(data[i][j])) > 3 and i >= 1  and j >= 1:
                pdf.multi_cell(col_width, 0.2, str(data[i][j]), border=1, align = 'C')        
            else:
                pdf.multi_cell(col_width, 0.4, str(data[i][j]), border=1, align = 'C')        
        pdf.set_xy(current_x + col_width, current_y)
        current_x = pdf.get_x()
    current_x = initial
    current_y = current_y + 0.4
    pdf.set_xy(current_x, current_y)
pdf.output('table-using-cell-borders.pdf','F')