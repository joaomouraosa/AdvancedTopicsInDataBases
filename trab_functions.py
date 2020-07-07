### codigo com algumas funcoes auxiliares para a animacao
import math
import numpy as np
import itertools as it
import random
import psycopg2
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register
import time
import csv
import copy

INFECTED=1 
NOT_INFECTED=0
SAVE_CSV=False
   
def dist(point1, point2):
    x1,y1=int(point1[0]),int(point1[1])
    x2,y2=int(point2[0]),int(point2[1])
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def setup_connection(name,user):
    conn = psycopg2.connect("dbname=%s user=%s" % (name,user))
    register(conn)
    cursor_psql = conn.cursor()
    return(conn,cursor_psql)

def query_database(query, cursor_psql):
    cursor_psql.execute(query)
    return cursor_psql.fetchall()

def get_taxis(n,array, cursor_psql):

    query = '''
    select distrito from cont_aad_caop2018 where st_within(st_setsrid(st_makepoint(%d,%d),3763), proj_boundary)
    '''

    taxis_porto=[]
    taxis_lisboa=[]
    added=[]
    
    for r in range(0,len(array)):
        for c in range(0,len(array[r])):
            taxi_x=array[r][c][0]
            taxi_y=array[r][c][1]

            if(taxi_x==0 and taxi_y==0): #podemos passar a frente dos taxis que estao no ponto 0 0 ja que nao estao activos e 0 0 nao esta dentro do porto ou de liesboa
                continue           
            cursor_psql.execute(query % (taxi_x,taxi_y))
            results=cursor_psql.fetchall()
            if(results[0][0]=='PORTO'):
                if(len(taxis_porto)<10 and c not in added):
                    taxis_porto.append([r,c])
                    added.append(c)
            if(results[0][0]=='LISBOA'):
                if(len(taxis_lisboa)<10 and c not in added):
                    taxis_lisboa.append([r,c])
                    added.append(c)
            if(len(taxis_porto)==10 and len(taxis_lisboa)==10):
                del added
                return (taxis_porto, taxis_lisboa)
    del added
    return (taxis_porto, taxis_lisboa)
        
def calculate_epidemic(array,ts_i,prob, distance, conn,cursor_psql,SAVE_CSV=True,recovered=False):
    recovered=[0 for i in len(OFFSETS[0])]
    
    n_rows = len(array) #number of timestamps
    n_cols = len(array[0]) #number of taxis
    
    infected = np.full((n_rows, n_cols), NOT_INFECTED)
    step=10

    first_10_taxis_porto, first_10_taxis_lisboa=get_taxis(10,array,cursor_psql)
    
    #escolher um taxi aleatorio do porto e outro de lisboa
    random_index=random.randint(0,9)
    porto = first_10_taxis_porto[random_index]
    lisboa= first_10_taxis_lisboa[random_index]

    #marca os 2 taxis escolhidos como infectados para todos os timestamps a partir do timestamp em que comecaram a circular

    for row in range(porto[0],n_rows):
        infected[row][porto[1]]=INFECTED
        
    for row in range(lisboa[0],n_rows):
        infected[row][lisboa[1]]=INFECTED

    for row in range(0,n_rows):
        starttime=time.time()

        for n_col1 in range(0,n_cols-1):

            COL1_INFECTED=False
            if(infected[row][n_col1]==INFECTED):
                COL1_INFECTED=True
                
            if(int(array[row][n_col1][0])==0): #se o taxi1 tiver coordenadas 0 0, significa que nao esta activo, e nao vai ser considerado
                continue        
            for n_col2 in range(n_col1+1,n_cols):
                if(int(array[row][n_col2][0])==0): #se o taxi2 tiver coordenadas 0 0, tambem nao vai ser considerado
                    continue

                COL2_INFECTED=False
                if(infected[row][n_col2]==INFECTED):
                    COL2_INFECTED=True
                    
                if(not COL1_INFECTED and not COL2_INFECTED): #se nenhum dos dois taxis esta infectado, nenhum vai infectar o outro, podemos passar para o proximo taxi
                    continue
                if(COL1_INFECTED and COL2_INFECTED): #se os dois ja estiverem infectados, tambem podemos avancar para o proximo
                    continue
                              
                INFECT=False
                if(random.randint(int(prob*10),10)==10): #probabilidade p de haver infeccao em 10s.
                    INFECT=True

                if (INFECT):
                    if(dist(array[row][n_col1],array[row][n_col2])<=distance):
                        if(COL1_INFECTED): #se o primeiro estiver infectado e o segundo nao, infectar o segundo
                            if (not SAVE_CSV):
                                print(array[row][n_col1][0], " " , array[row][n_col1][1], " ",array[row][n_col2][0], " ",array[row][n_col2][1])
                            for r in range(row,n_rows):
                                infected[r][n_col2]=INFECTED
                        else:
                            if (not SAVE_CSV):
                                print(array[row][n_col1][0], " " , array[row][n_col1][1], " ",array[row][n_col2][0], " ",array[row][n_col2][1])
                            for r in range(row,n_rows):
                                infected[r][n_col1]=INFECTED
        if(not SAVE_CSV):
            print('row %d took %f' % (row,time.time()-starttime))

    if(SAVE_CSV):
        for row in infected:
            print("%f" %(row[0]),end='')
            for col in range(1,len(row)):
                print(",%f" %(row[col]),end='')
            print("")

    return infected
"""
def getHistogramData(array):
    n_taxis = len(array[0])
    hist={}
    for n_row in range(0,len(array)):
        hist[n_row]=0
        for n_col in range(0,len(array[n_row])):
            if(array[n_row][n_col]==INFECTED):
                hist[n_row]+=1

    histx = [[0,0],[0,0]]
    histy = [[0,0],[0,0]]

    for i in range(2,len(hist.keys())):
        histx.append(histx[i-1] + [i])
        histy.append (histy[i-1] + [hist[i]])

    histy_ninf=copy.deepcopy(histy)

    for i in range(0,len(histy)):
        for j in range(0,len(histy[i])):
            histy_ninf[i][j]=1600-histy[i][j]

    histx=np.array(histx)
    histy=np.array(histy)
    histy_ninf=np.array(histy_ninf)
    return (histx,histy,histy_ninf)
"""                           

def read_csv(csv_file):
    array = []
    with open(csv_file, 'r') as csvFile:
        reader = csv.reader(csvFile)
        i = 0
        for row in reader:
            l = []
            for j in row:
                l.append(float(j))
            array.append(l)
    return array


def read_offsets(file_name):
    offsets = []
    with open(file_name, 'r') as csvFile:
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
    return offsets
#import trab_functions as aux
#aux.write_offsets([1,2,3])


def calculate_epidemic_with_imunity(array,ts_i,prob, distance, conn,cursor_psql,SAVE_CSV=True,recovered=False):
    recovered=[0 for i in len(OFFSETS[0])]

    n_rows = len(array) #number of timestamps
    n_cols = len(array[0]) #number of taxis

    infected = np.full((n_rows, n_cols), NOT_INFECTED)
    step=10

    first_10_taxis_porto, first_10_taxis_lisboa=get_taxis(10,array,cursor_psql)

    #escolher um taxi aleatorio do porto e outro de lisboa
    random_index=random.randint(0,9)
    porto = first_10_taxis_porto[random_index]
    lisboa= first_10_taxis_lisboa[random_index]

    #marca os 2 taxis escolhidos como infectados para todos os timestamps a partir do timestamp em que comecaram a circular

    for row in range(porto[0],n_rows):
        infected[row][porto[1]]=INFECTED

    for row in range(lisboa[0],n_rows):
        infected[row][lisboa[1]]=INFECTED

    for row in range(0,n_rows):
        starttime=time.time()

        for n_col1 in range(0,n_cols-1):

            COL1_INFECTED=False
			COL1_RECOVERED=False
			if(infected[row][n_col1]>RECOVERED):
				if(infected[row][n_col1]==RECOVER_TIME):
					infected[row][n_col1]=RECOVERED
					COL1_RECOVERED=True
				else:
					infected[row][n_col1]+=1
					COL1_INFECTED=True

            if(infected[row][n_col1]==INFECTED):
                infected[row][n_col1]=3
				COL1_INFECTED=True

            if(int(array[row][n_col1][0])==0): #se o taxi1 tiver coordenadas 0 0, significa que nao esta activo, e nao vai ser considerado
                continue        
            for n_col2 in range(n_col1+1,n_cols):
                if(int(array[row][n_col2][0])==0): #se o taxi2 tiver coordenadas 0 0, tambem nao vai ser considerado
                    continue

                COL2_INFECTED=False
				COL2_RECOVERED=False
                if(infected[row][n_col2]==INFECTED):
                    COL2_INFECTED=True
				if(infected[row][n_col2]==RECOVERED):
                    COL2_RECOVERED=True     
                if(not COL1_INFECTED and not COL2_INFECTED): #se nenhum dos dois taxis esta infectado, nenhum vai infectar o outro, podemos passar para o proximo taxi
                    continue
                if(COL1_INFECTED and COL2_INFECTED): #se os dois ja estiverem infectados, tambem podemos avancar para o proximo
                    continue
                if(COL2_RECOVERED or COL1_RECOVERED): #se um dos dois estiver imune, não irá haver infeção
					continue
                INFECT=False
                if(random.randint(int(prob*10),10)==10): #probabilidade p de haver infeccao em 10s.
                    INFECT=True

                if (INFECT):
                    if(dist(array[row][n_col1],array[row][n_col2])<=distance):
                        if(COL1_INFECTED): #se o primeiro estiver infectado e o segundo nao, infectar o segundo
                            if (not SAVE_CSV):
                                print(array[row][n_col1][0], " " , array[row][n_col1][1], " ",array[row][n_col2][0], " ",array[row][n_col2][1])
                            for r in range(row,n_rows):
                                infected[r][n_col2]=INFECTED
                        else:
                            if (not SAVE_CSV):
                                print(array[row][n_col1][0], " " , array[row][n_col1][1], " ",array[row][n_col2][0], " ",array[row][n_col2][1])
                            for r in range(row,n_rows):
                                infected[r][n_col1]=INFECTED
        if(not SAVE_CSV):
            print('row %d took %f' % (row,time.time()-starttime))

    if(SAVE_CSV):
        for row in infected:
            print("%f" %(row[0]),end='')
            for col in range(1,len(row)):
                print(",%f" %(row[col]),end='')
            print("")

    return infected
