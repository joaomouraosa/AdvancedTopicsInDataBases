import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import math
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import datetime
import csv
from postgis import Polygon,MultiPolygon
from postgis.psycopg import register


DB_NAME='public'
DB_USER='joao'

def animate(i):
    ax.set_title(datetime.datetime.utcfromtimestamp(ts_i+i*10))
    scat.set_offsets(offsets[i])

scale=1/3000000
conn = psycopg2.connect("dbname=%s user=%s" % (DB_NAME,DB_USER))
register(conn)

ts_i= 1570665600
ts_f= 1570667000

xs_min, xs_max, ys_min, ys_max = -120000, 165000, -310000, 285000
width_in_inches  = (xs_max-xs_min)/0.0254*1.1
height_in_inches = (ys_max-ys_min)/0.0254*1.1

fig, ax = plt.subplots(figsize=(width_in_inches*scale, height_in_inches*scale))
ax.axis('off')
ax.set(xlim=(xs_min, xs_max), ylim=(ys_min, ys_max))

cursor_psql = conn.cursor()

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

scat = ax.scatter(x,y,s=2,color='orange')
anim = FuncAnimation(    fig, animate, interval=10, frames=len(offsets)-1, repeat = False)

plt.draw()
plt.show()

#Writer = animation.writers['ffmpeg']
#writer = Writer(fps=20, metadata=dict(artist='me'),bitrate=1800)
#anim.save('animation.mp4', writer=writer)

conn.close()

