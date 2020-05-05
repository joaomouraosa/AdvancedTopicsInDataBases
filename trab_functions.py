### codigo com algumas funcoes auxiliares para a animacao
import math
import numpy
import itertools as it
import random
import psycopg2
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register

INFECTED=.2 #codigo da cor vermelha para a animacao. pareceu-me mais facil atribuir directamente a cor em vez dum valor booleano.
NOT_INFECTED=.3 #codigo da cor verde
SAVE_CSV=True


#def get_row(initial_timestamp, timestamp, step):
#    return float(timestamp-initial_timestamp)/step
    
def dist(point1, point2):
    x1,y1=int(point1[0]),int(point1[1])
    x2,y2=int(point2[0]),int(point2[1])
#    print((x1,y1),(x2,y2))
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def setup_connection(name,user):
    conn = psycopg2.connect("dbname=%s user=%s" % (name,user))
    register(conn)
    cursor_psql = conn.cursor()
    return(conn,cursor_psql)

def query_database(query, cursor_psql):
    cursor_psql.execute(query)
    return cursor_psql.fetchall()

#def get_random_taxis(n,concelho, cursor_psql):
#    results = query_database(
#        '''select id,ts from tracks join cont_aad_caop2018 on(st_contains(cont_aad_caop2018.proj_boundary, st_startpoint(proj_track))) where concelho='%s' order by ts asc limit 10''' % concelho,
#        cursor_psql)
#    random_row=random.randint(0,9)
#    taxi_id=results[random_row][0]
#    taxi_ts=results[random_row][1]
#    return(taxi_id,taxi_ts)
    
#def get_random_taxis2(n_rows,n_cols,array):
#
#    portoX=-41218
#    portoY=166083
#    lisboaX=-88795
#    lisboaY=-102455
#
#    diffPortoX=10000
#    diffLisboaX=15000
#    diffPortoY=10000
#    diffLisboaY=15000
#    taxis_porto=[]
#    taxis_lisboa=[]
#
#    for row in range(0,n_rows):
#        for col in range(0,n_cols):
#            if(len(taxis_porto)<10 and (array[row][col][0]!=0) and abs(array[row][col][0]-portoX)<diffPortoX and (abs(array[row][col][1]-portoY)<diffPortoY) and ([row,col] not in taxis_porto)):
#                taxis_porto.append([row,col])
#            if(len(taxis_lisboa)<10 and (array[row][col][0]!=0) and abs(array[row][col][0]-lisboaX)<diffLisboaX and (abs(array[row][col][1]-lisboaY)<diffLisboaY) and ([row,col] not in taxis_lisboa)):
#                taxis_lisboa.append([row,col])
#            if (len(taxis_lisboa)==10 and len(taxis_porto)==10):
#                print("coordinates porto")
#                print(taxis_porto)
#                print("coordinates lisboa")
#                print(taxis_lisboa)
#                random_index = random.randint(0,9)
#                return(taxis_porto[random_index],taxis_lisboa[random_index])

def calculate_epidemic(array,ts_i,conn,cursor_psql,SAVE_CSV):
    n_rows = len(array) #number of timestamps
    n_cols = len(array[0]) #number of taxis

    infected = numpy.full((n_rows, n_cols), NOT_INFECTED)   
    step=10

    #tirar 1 aleatoriamente em lisboa e no porto
#    porto, lisboa = get_random_taxis2(n_rows,n_cols,array)

    #linha(timestamp) e coluna(taxi) dos primeiros 10 taxis a iniciarem o seu movimento no porto e em lisboa
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
        print(row)
        for n_col1,n_col2 in it.combinations(range(0,n_cols),2): #comparar todos os pares diferentes de colunas(taxis)
            if(dist(array[row][n_col1],array[row][n_col2])<=50):
                random_value= random.randint(1,10) #probabilidade (10%) de um taxi infectar outro, estando a 50 ou menos metros de distancia
#                random_value=1
                if(infected[row][n_col1] and not (infected[row][n_col2]) and random_value==1): #se o primeiro estiver infectado e o segundo nao, infectar o segundo
                    for r in range(row,n_rows):
                        infected[r][n_col2]=INFECTED
                if(infected[row][n_col2] and not (infected[row][n_col1]) and random_value==1): #se o segundo estiver infectado e o segundo nao, infectar o segundo
                    for r in range(row,n_rows):
                        infected[r][n_col1]=INFECTED
#        print(infected)
#        print(infected[row])
#        print(infected[row][porto[1]])
#        print(infected[row][lisboa[1]])

    SAVE_CSV=True
    if(SAVE_CSV):
        for row in infected:
            print("%f" %(row[0]),end='')
            for col in range(1,len(row)):
                print(",%f" %(row[col]),end='')
            print("")

    return infected
