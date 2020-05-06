### codigo com algumas funcoes auxiliares para a animacao
import math
import numpy
import itertools as it
import random
import psycopg2
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register
import time

INFECTED=.2 #codigo da cor vermelha para a animacao. pareceu-me mais facil atribuir directamente a cor em vez dum valor booleano.
NOT_INFECTED=.3 #codigo da cor verde
SAVE_CSV=False

#def get_row(initial_timestamp, timestamp, step):
#    return float(timestamp-initial_timestamp)/step
    
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

def calculate_epidemic(array,ts_i,conn,cursor_psql,SAVE_CSV):
    n_rows = len(array) #number of timestamps
    n_cols = len(array[0]) #number of taxis

    infected = numpy.full((n_rows, n_cols), NOT_INFECTED)   
    step=10

    #tirar 1 aleatoriamente em lisboa e no porto
    pos_first10_taxis_porto=[[3, 161], [3, 187], [4, 161], [4, 187], [4, 247], [5, 161], [5, 187], [5, 247], [5, 978], [6, 161]]
    pos_first10_taxis_lisboa=[[1, 836], [1, 1163], [2, 836], [2, 1163], [2, 1285], [2, 1564], [3, 836], [3, 1163], [3, 1285], [3, 1564]]

    #escolher um taxi aleatorio do porto e outro de lisboa
    random_index=random.randint(0,9)
    porto = pos_first10_taxis_porto[random_index] #[row,col]
    lisboa= pos_first10_taxis_lisboa[random_index]
#    print(porto)
#    print(lisboa)

    #marca os 2 taxis escolhidos como infectados para todos os timestamps a partir do timestamp em que começaram a circular
    infected[porto[0]][porto[1]]=INFECTED
    for row in range(porto[0],n_rows):
        infected[row][porto[1]]=INFECTED
        
    infected[lisboa[0]][lisboa[1]]=INFECTED
    for row in range(lisboa[0],n_rows):
        infected[row][lisboa[1]]=INFECTED

    for row in range(0,n_rows):
        starttime=time.time()
        for n_col1,n_col2 in it.combinations(range(0,n_cols),2): #comparar todos os pares diferentes de colunas(taxis)
            INFECT=False
            
            random_value= random.randint(1,10)
            for i in range(0,step):
                if (random_value==1):
                    INFECT=True
                    break

            if (INFECT):
                if(dist(array[row][n_col1],array[row][n_col2])<=50):
                    if(infected[row][n_col1]==INFECTED and infected[row][n_col2]==NOT_INFECTED): #se o primeiro estiver infectado e o segundo nao, infectar o segundo
                        for r in range(row,n_rows):
                            infected[r][n_col2]=INFECTED
                    if(infected[row][n_col2]==INFECTED and infected[row][n_col1]==NOT_INFECTED): #se o segundo estiver infectado e o segundo nao, infectar o segundo
                        for r in range(row,n_rows):
                            infected[r][n_col1]=INFECTED
        if(not SAVE_CSV):
            print('row %d took %d' % (row,time.time()-starttime))

    if(SAVE_CSV):
        for row in infected:
            print("%f" %(row[0]),end='')
            for col in range(1,len(row)):
                print(",%f" %(row[col]),end='')
            print("")

    return infected
