#gera o array 2d com a epidemia, para ser guardado num ficheiro .csv
#para guarda-lo num ficheiro epidemic.csv: python generate_epidemic.py > epidemic.csv
import math
import numpy
import itertools as it
import random
import psycopg2
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register
import trab_functions
import csv

SAVE_CSV=True
ts_i= 1570665600

#ler o csv com os offsets
offsets = []
with open('offsets3.csv', 'r') as csvFile:
    reader = csv.reader(csvFile)
    i = 0
    for row in reader:
        l = []
        for j in row:
            x,y = j.split()
            x = float(x)
            y= float(y)
            l.append([x,y])
        offsets.append(l)
x,y = [],[]
for i in offsets[0]:
    x.append(i[0])
    y.append(i[1])


#criar a epidemia
#trab_functions.calculate_epidemic(offsets,ts_i,None, None, SAVE_CSV)

#criar epidemia com recuperados
trab_functions.calculate_epidemic_with_imunity(offsets,ts_i,None, None, SAVE_CSV)
