from fpdf import FPDF

pdf=FPDF(format='letter', unit='in')
pdf.add_page()
 
pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
pdf.set_font('DejaVu', '', 14)
 
epw = pdf.w - 2*pdf.l_margin
 
col_width = epw/4
 
data= [['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', ''],
       ['', '', '', '', '', '', '', '', '', '']]

pdf.set_font('DejaVu', '', 14)
pdf.cell(epw, 0.0, 'Карта пациента', align='C')
pdf.set_font('DejaVu', '', 14)
pdf.ln(0.5)
 
th = pdf.font_size


pdf.set_font('DejaVu', '', 14)
pdf.cell(epw, 0.0, 'With more padding', align='C')
pdf.set_font('DejaVu', '', 14)
pdf.ln(0.5)
 
for row in data:
    for datum in row:
        pdf.cell(col_width, 2*th, str(datum), border=1)
    pdf.ln(2*th)

pdf.output('table-using-cell-borders.pdf','F')