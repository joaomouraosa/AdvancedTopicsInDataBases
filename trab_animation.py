import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import psycopg2
import math
from matplotlib.animation import FuncAnimation
import datetime
import csv
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register
import trab_functions
from matplotlib import cm
import time

DEBUG=True

def animate(i, color_data, scat):
    ax.set_title(datetime.datetime.utcfromtimestamp(ts_i+i*10))
    scat.set_array(color_data[i])
    scat.set_offsets(offsets[i])

scale=1/3000000
DB_NAME='tracks'
DB_USER='nan'

conn, cursor_psql =  trab_functions.setup_connection(DB_NAME,DB_USER)
#conn = psycopg2.connect("dbname=public user=joao")
#register(conn)

ts_i= 1570665600

starttime=time.time()

xs_min, xs_max, ys_min, ys_max = -120000, 165000, -310000, 285000
width_in_inches  = (xs_max-xs_min)/0.0254*1.1
height_in_inches = (ys_max-ys_min)/0.0254*1.1

fig, ax = plt.subplots(figsize=(width_in_inches*scale, height_in_inches*scale))
ax.axis('off')
ax.set(xlim=(xs_min, xs_max), ylim=(ys_min, ys_max))

#cursor_psql = conn.cursor()



sql = "select distrito,st_union(proj_boundary) from cont_aad_caop2018 group by distrito"

cursor_psql.execute(sql)
results = cursor_psql.fetchall()
xs , ys = [],[]

for row in results:
    geom = row[1]
    if type(geom) is MultiPolygon:
        for pol in geom:
            xys = pol[0].coords
            xs, ys = [],[]
            for (x,y) in xys:
                xs.append(x)
                ys.append(y)
            ax.plot(xs,ys,color='black',lw='0.2')
    if type(geom) is Polygon:
        xys = geom[0].coords
        xs, ys = [],[]
        for (x,y) in xys:
            xs.append(x)
            ys.append(y)
        ax.plot(xs,ys,color='black',lw='0.2')

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

if DEBUG: print("part 1 took: %d" % (time.time()-starttime))
starttime=time.time()

#todo

#infected = np.random.random((8640,1660))
infected= trab_functions.read_csv('epidemic.csv')
infected=np.array(infected)

if DEBUG: print("part 2 took: %d" % (time.time()-starttime))
starttime=time.time()

green, red=.2, .5
num_taxis=len(offsets[0])
half=int(num_taxis/2)
rest=num_taxis-half

colors1, colors2 = np.full(half,green), np.full(rest,red)
colors=[*colors1,*colors2]

#scat = ax.scatter(x,y,s=2)
scat = ax.scatter(x,y,c=colors,s=2, cmap=mpl.cm.Set1)

anim = FuncAnimation(fig, animate, interval=10, frames=len(offsets)-1, repeat = False , fargs=(infected,scat))

plt.draw()
plt.show()

if DEBUG: print("part 3 took: %d" % (time.time()-starttime))
#starttime=time.time()

conn.close()
