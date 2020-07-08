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
RECOVERED=2
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
        
def calculate_epidemic(array,ts_i,prob=.10, distance=50, SAVE_CSV=True,immunity_mode=False):
    SAVE_CSV=False
    conn = psycopg2.connect("dbname=tracks user=nan")
    cursor_psql = conn.cursor()

    n_rows = len(array) #number of timestamps
    n_cols = len(array[0]) #number of taxis

    recovery_counter = [0 for i in range(0,n_cols)]
    RECOVERY_TIME = 360*6 #6 horas
    
    infected = np.full((n_rows, n_cols), NOT_INFECTED)
        
    first_10_taxis_porto, first_10_taxis_lisboa=get_taxis(10,array,cursor_psql)
    
    #escolher um taxi aleatorio do porto e outro de lisboa
    random_index=random.randint(0,9)
    porto = first_10_taxis_porto[random_index]
    lisboa= first_10_taxis_lisboa[random_index]

    #marca os 2 taxis escolhidos como infectados para todos os timestamps a partir do timestamp em que comecaram a circular
    for row in range(porto[0],n_rows):
        infected[row][porto[1]]=INFECTED
    recovery_counter[porto[1]]=1
        
    for row in range(lisboa[0],n_rows):
        infected[row][lisboa[1]]=INFECTED
    recovery_counter[lisboa[1]]=1
        
    for row in range(0,n_rows):
        starttime=time.time()

        for n_col1 in range(0,n_cols-1):

            COL1_INFECTED, COL1_RECOVERED=False, False

            if (immunity_mode and infected[row][n_col1]==RECOVERED):
                continue
            
            if(infected[row][n_col1]==INFECTED):
                COL1_INFECTED=True
                recovery_counter[n_col1]+=1

                if(immunity_mode and recovery_counter[n_col1]>=RECOVERY_TIME):
                    for r in range(row,n_rows):
                        infected[r][n_col1]=RECOVERED
                        COL1_RECOVERED=True
                
            if(int(array[row][n_col1][0])==0): #se o taxi1 tiver coordenadas 0 0, significa que nao esta activo, e nao vai ser considerado
                continue
            if(immunity_mode and COL1_RECOVERED): #o taxi esta recuperado, nao vai infectar nem ser infectado
                continue
            
            for n_col2 in range(n_col1+1,n_cols):
                if(int(array[row][n_col2][0])==0): #se o taxi2 tiver coordenadas 0 0, tambem nao vai ser considerado
                    continue
                
                if (immunity_mode and infected[row][n_col2]==RECOVERED):
                    continue
                
                COL2_INFECTED, COL2_RECOVERED=False, False
                if(infected[row][n_col2]==INFECTED):
                    COL2_INFECTED=True

                if(immunity_mode and COL2_INFECTED and recovery_counter[n_col2]>=RECOVERY_TIME):
                    for r in range(row,n_rows):
                        infected[r][n_col2]=RECOVERED
                        COL2_RECOVERED=True
    
                if(not COL1_INFECTED and not COL2_INFECTED): #se nenhum dos dois taxis esta infectado, nenhum vai infectar o outro, podemos passar para o proximo taxi
                    continue
                if(COL1_INFECTED and COL2_INFECTED): #se os dois ja estiverem infectados, tambem podemos avancar para o proximo
                    continue
                if(immunity_mode and COL2_RECOVERED): #se o segundo taxi esta recuperado, nao vai infectar o anterior
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
                            recovery_counter[n_col2]+=1
                                
                        else:
                            if (not SAVE_CSV):
                                print(array[row][n_col1][0], " " , array[row][n_col1][1], " ",array[row][n_col2][0], " ",array[row][n_col2][1])
                            for r in range(row,n_rows):
                                infected[r][n_col1]=INFECTED
                            recovery_counter[n_col1]+=1
        if(not SAVE_CSV):
            print('row %d took %f' % (row,time.time()-starttime))

    if(SAVE_CSV):
        for row in infected:
            print("%f" %(row[0]),end='')
            for col in range(1,len(row)):
                print(",%f" %(row[col]),end='')
            print("")

    return infected

def get_histograms(distritos, infected, OFFSETS, cursor_psql):
    S, I, R = 0, 1, 2
    hist={}
    step=120
    n=int(len(infected)/step)
    inf_pos, rec_pos =[], []

    '''inicializar os histogramas'''
    for d in distritos:
        hist[d]={}
        for s in ["S","I","R"]:
            hist[d][s]=[0]*n
        
    def within(point):
        x,y=float(point[0]),float(point[1])
        if (x==0 and y==0):
            return "NOT_ACTIVE"
    
        query=  '''
            SELECT distrito 
            FROM cont_aad_caop2018
            WHERE st_within(ST_SetSRID(ST_Point( %f, %f), 3763), proj_boundary) 
            ''' % (x,y)
        cursor_psql.execute(query)
        results = cursor_psql.fetchall()
        if (not results):
            return "NOT_ACTIVE"
        return str(results[0][0])
    k=0

    for i in range(0,len(infected),step):
        for j in range(0,len(infected[i])):
            d=within(OFFSETS[i][j])
            if (d!="NOT_ACTIVE"):
                if (infected[i][j]==I and j not in inf_pos):
                    if(d in distritos):
                        hist[d]["I"][k]+=1
                    hist["*"]["I"][k]+=1
                    inf_pos.append(j)

                if (infected[i][j]==R and j not in rec_pos):
                    hist["*"]["R"][k]+=1               
                    hist["*"]["S"][k]-=1
                    hist["*"]["I"][k]-=1
                    rec_pos.append(j)

        if (k>0):
            for d in distritos:
                hist[d]["I"][k]+=hist[d]["I"][k-1]
                hist[d]["R"][k]+=hist[d]["R"][k-1]
                hist["*"]["S"][k]=1660-hist["*"]["R"][k-1]-hist["*"]["I"][k-1]
        k+=1
    return hist


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



def show_map(results,map_plot, color_="black"):
    xs, ys = [],[]
    for row in results:
        geom = row[1]
        if type(geom) is MultiPolygon:
            for pol in geom:
                xys = pol[0].coords
                xs, ys = [],[]
                for (x,y) in xys:
                    xs.append(x)
                    ys.append(y)
                map_plot.plot(xs,ys,color=color_,lw='0.2',alpha=1)
        if type(geom) is Polygon:
            xys = geom[0].coords
            xs, ys = [],[]
            for (x,y) in xys:
                xs.append(x)
                ys.append(y)
            map_plot.plot(xs,ys,color=color_, lw='0.2',alpha=1)

def update_map(results,map_plot, timestamp):
    xs, ys = [],[]
    for row in results:
        geom = row[1]
        if type(geom) is MultiPolygon:
            for pol in geom:
                xys = pol[0].coords
                xs, ys = [],[]
                for (x,y) in xys:
                    xs.append(x)
                    ys.append(y)
                map_plot.plot(xs,ys,color='red',lw='0.2',alpha=1)
        if type(geom) is Polygon:
            xys = geom[0].coords
            xs, ys = [],[]
            for (x,y) in xys:
                xs.append(x)
                ys.append(y)
            map_plot.plot(xs,ys,color='red', lw='0.2',alpha=1)


def distritos_infetados(infected, OFFSETS, cursor_psql):
    dist={}
    step=120
    n=int(len(infected)/step)
    inf_pos, rec_pos =[], []
	
	cursor_psql.execute('''
                    SELECT st_union(proj_boundary) 
                    FROM cont_aad_caop2018
					GROUP BY distrito
                    ''')
	distritos  = cursor_psql.fetchall()

    '''inicializar os histogramas'''
    for d in distritos:
        dist[d]={}
        dist[d]=[False]*n
        
    def within(point):
        x,y=float(point[0]),float(point[1])
        if (x==0 and y==0):
            return "NOT_ACTIVE"
    
        query=  '''
            SELECT st_union(proj_boundary) 
            FROM cont_aad_caop2018
            WHERE st_within(ST_SetSRID(ST_Point( %f, %f), 3763), proj_boundary)
			GROUP BY distrito			
            ''' % (x,y)
        cursor_psql.execute(query)
        results = cursor_psql.fetchall()
        if (not results):
            return "NOT_ACTIVE"
        return str(results[0][0])
    k=0

    for i in range(0,len(infected),step):
        for j in range(0,len(infected[i])):
            d=within(OFFSETS[i][j])
            if (d!="NOT_ACTIVE"):
                if (infected[i][j]==I and j not in inf_pos):
                    if(d in distritos):
                        dist[d][k]=True
                    inf_pos.append(j)
        k+=1
    return dist