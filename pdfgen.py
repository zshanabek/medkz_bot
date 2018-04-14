#!/usr/bin/python
# -*- coding: utf-8 -*-
import src.utils
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import * 
from reportlab.lib.units import inch 

doc = SimpleDocTemplate("map.pdf", pagesize=letter)
# container for the 'Flowable' objects
elements = []

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

for j in range(3):
    data[0][j] = src.utils.illnesses[j]['graft_name']
t=Table(data)
t.setStyle(TableStyle([('FONTNAME',(0,0),(5,0),'Times-Roman')]))
elements.append(t)
# write the document to disk
doc.build(elements)