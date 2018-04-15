from fpdf import FPDF
import src.utils
import pdb

from pymongo import MongoClient
client = MongoClient('mongodb://zshanabek:451524aa@ds111078.mlab.com:11078/medkzbot_db')

db = client.medkzbot_db
patients = db.patients
grafts = patients.find_one({'telegram_id': 483742281})['grafts']
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

k = 1
n = 1



# def find_point(i, j):
    

# for i in range(0, 10):
#     for j in range(0, 10):
#         find_point(i,j)

def put_status(graft_id, date_id):
    current_date = next((item for item in grafts[graft_id]['dates'] if item['date_id'] == date_id))
    print(current_date)
    graft_id += 1
    data[graft_id][date_id] =current_date['status']
for graft in grafts:
    print(str(graft['graft_id']) + ": " + graft['graft_name'])
    for date in graft['dates']:
        put_status(graft['graft_id'], date['date_id'])
pdf.set_font('DejaVu', '', 14)
pdf.cell(epw, 0.0, 'Карта пациента', align='C')
pdf.set_font('DejaVu', '', 6)
pdf.ln(0.5)
 
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
            pdf.multi_cell(col_width, 0.4, str(data[i][j]), border=1, align = 'C')        
        pdf.set_xy(current_x + col_width, current_y)
        current_x = pdf.get_x()
    current_x = initial
    current_y = current_y + 0.4
    pdf.set_xy(current_x, current_y)
pdf.output('table-using-cell-borders.pdf','F')