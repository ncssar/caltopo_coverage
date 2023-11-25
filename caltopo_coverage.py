# caltopo_coverage.py
# create coverage images (png) of caltopo tiles dir

import os
from glob import glob
import json
# import png
# import numpy
# import imageio
from PIL import Image,ImageDraw,ImageFont

tiles_dir='.'
cd={}

# cd is the coverage dict - a dict of dicts of dicts of lists, like so:
#    "mvum-2m": {
#       "38": {
#          "119": [
#             "32",
#             "33"
#          ]
#       },
#       "39": {
#          "119": [
#             "02",
#             "03"
#          ]
#       }
#    },
#    "mvum": {
#       "38": {
#          "119": [
#             "32",
#             "33"
#          ]
#       },
#       "39": {
#          "119": [
#             "02",
#             "03"
#          ]
#       }
#    },

# seed min and max bounds
latMin=999
latMax=0
lonMin=999
lonMax=0

files=[f for f in os.listdir(tiles_dir) if os.path.isfile(f) and f.endswith('.mbtiles')]
# print(str(files))
for file in files:
	file=os.path.splitext(file)[0] # remove .mbtiles extension
	parse=file.split('-')
	if len(parse)==5:
		layer='-'.join(parse[0:2])
		[lat,lon,grid]=parse[2:]
	elif len(parse)==4:
		[layer,lat,lon,grid]=parse
	else:
		print('WARNING: skipping invalid tile filename: '+file)
		continue
	print('LAYER: '+layer+'  lat='+lat+'  lon='+lon+'  grid='+grid)
	# build cd
	if layer not in cd.keys():
		cd[layer]={}
	if lat not in cd[layer].keys():
		cd[layer][lat]={}
	if lon not in cd[layer][lat].keys():
		cd[layer][lat][lon]=[]
	cd[layer][lat][lon].append(grid)
	# determine boundaries
	lat=int(lat)
	lon=int(lon)
	if lat<latMin:
		latMin=lat
	elif lat>latMax:
		latMax=lat
	if lon<lonMin:
		lonMin=lon
	elif lon>lonMax:
		lonMax=lon
print(json.dumps(cd,indent=3))

# for now, hardcode image boundaries
# latMin=31
# latMax=43
# lonMin=112
# lonMax=126

# determine lat and lon bounds based on existing filenames

# latMin=39
# latMax=43
# lonMin=119
# lonMax=122

minorGridLineWidth=1
majorGridLineWidth=2
minorGridSize=20 # pitch, i.e. gridlines are drawn on top of filled rectangles of this size
majorGridSize=minorGridSize*4
# pixPerMinorGrid=minorGridFillPixels+minorGridLineWidth
# pixPerMajorGrid=4*pixPerMinorGrid+majorGridLineWidth
# xOffset=lonMin*4
# yOffset=latMin*4

h=(latMax-latMin+1)*majorGridSize
w=(lonMax-lonMin+1)*majorGridSize
[llX,llY]=[0,h] # ll=lower left
[urX,urY]=[w,0] # ur=upper right

for layer in cd.keys():
	# # see https://discuss.python.org/t/create-png-image-from-coordinates/16691/2
	# image=numpy.zeros((h,w,3),dtype=numpy.uint8)
	# for lat in cd[layer].keys():
	# 	for lon in cd[layer][lat].keys():
	# 		for grid in cd[layer][lat][lon]:
	# 			x=int(lon)*4+int(grid[1])-xOffset # [western-hemisphere] lon and second char of grid both increase westward
	# 			y=int(lat)*4+int(grid[0])-yOffset # lat and first char of grid both increase northward
	# 			image[x,y,:]=(0xFF,0,0)
	# imageio.imwrite(layer+'_coverage.bmp',image)
	im=Image.new(mode='RGB',size=(w+40,h+40)) # +40 in each dimension, for label area
	font=ImageFont.truetype('arial.ttf', 16)
	draw=ImageDraw.Draw(im)

	# fill grids as appropriate
	for lat in cd[layer].keys():
		print('lat:'+str(lat))
		for lon in cd[layer][lat].keys():
			majorGridLeft=urX-((int(lon)-lonMin)*majorGridSize)
			majorGridTop=llY-((int(lat)-latMin)*majorGridSize)
			print('  lon:'+str(lon)+'  left='+str(majorGridLeft)+' top='+str(majorGridTop))
			for grid in cd[layer][lat][lon]:
				print('    grid:'+str(grid))
				[gridY,gridX]=grid # two-character subgrid name
				gridX=int(gridX)
				gridY=int(gridY)
				# pillow 10 docs say that pillow rectangle coords are a 4-tuple: left, bottom, width, height
				# BUT that's wrong: for pillow 9.1 and 10.0, it should be: x0(left), y0(top), x1(right), y1(bottom)
				#  also note that pillow 10 requires x0 <= x1 and y0 <= y1 (pillow 9.1 didn't require this)
				minorGridLeft=majorGridLeft-(gridX*minorGridSize)
				minorGridTop=majorGridTop-(gridY*minorGridSize)
				rect=(
					minorGridLeft-minorGridSize+1,
					minorGridTop-minorGridSize+1,
					minorGridLeft,
					minorGridTop)
				print('      rect:'+str(rect))
				draw.rectangle(rect,fill=(0,200,0))

	# draw gridlines
	# draw all minor gridlines first, then draw all major gridlines on top
	minorLineList=[]
	majorLineList=[]
	for lat in range(latMin,latMax+1):
		# draw major grid (horizontal lines)
		y=llY-((lat-latMin)*majorGridSize)
		points=[(llX,y),(urX,y)]
		majorLineList.append(points)
		# draw label
		draw.text((w+20,y-int(majorGridSize/2)),str(lat),font=font,anchor='mm',fill=(200,200,200))
		# draw minor grid (horizontal lines)
		# y-=majorGridLineWidth # reduce y by grid line width difference, to prep for the following loop
		for i in [1,2,3]:
			y-=minorGridSize
			points=[(llX,y),(urX,y)]
			minorLineList.append(points)
	for lon in range(lonMin,lonMax+1):
		# draw major grid (vertical lines)
		x=urX-((lon-lonMin)*majorGridSize)+1
		points=[(x,llY),(x,urY)]
		majorLineList.append(points)
		# draw label
		draw.text((x-int(majorGridSize/2),h+20),str(lon),font=font,anchor='mm',fill=(200,200,200))
		# draw minor grid (horizontal lines)
		# x-=majorGridLineWidth # reduce x by grid line width difference, to prep for the following loop
		for i in [1,2,3]:
			x-=minorGridSize
			points=[(x,llY),(x,urY)]
			minorLineList.append(points)
	for points in minorLineList:
		draw.line(points,fill=(128,128,0),width=minorGridLineWidth)
		print('drawing minor gridline: '+str(points))
	for points in majorLineList:
		draw.line(points,fill=(255,255,255),width=majorGridLineWidth)
		print('drawing major gridline: '+str(points))

	im.save(layer+'_coverage.png','PNG')




