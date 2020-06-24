# %%
"""
<table class="ee-notebook-buttons" align="left">
    <td><a target="_blank"  href="https://github.com/giswqs/geemap/tree/master/examples/template/template.ipynb"><img width=32px src="https://www.tensorflow.org/images/GitHub-Mark-32px.png" /> View source on GitHub</a></td>
    <td><a target="_blank"  href="https://nbviewer.jupyter.org/github/giswqs/geemap/blob/master/examples/template/template.ipynb"><img width=26px src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Jupyter_logo.svg/883px-Jupyter_logo.svg.png" />Notebook Viewer</a></td>
    <td><a target="_blank"  href="https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/template/template.ipynb"><img src="https://www.tensorflow.org/images/colab_logo_32px.png" /> Run in Google Colab</a></td>
</table>
"""

# %%
"""
## Install Earth Engine API and geemap
Install the [Earth Engine Python API](https://developers.google.com/earth-engine/python_install) and [geemap](https://github.com/giswqs/geemap). The **geemap** Python package is built upon the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) packages and implements several methods for interacting with Earth Engine data layers, such as `Map.addLayer()`, `Map.setCenter()`, and `Map.centerObject()`.
The following script checks if the geemap package has been installed. If not, it will install geemap, which automatically installs its [dependencies](https://github.com/giswqs/geemap#dependencies), including earthengine-api, folium, and ipyleaflet.

**Important note**: A key difference between folium and ipyleaflet is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying static data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). Note that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet ([source](https://github.com/googlecolab/colabtools/issues/60#issuecomment-596225619)). Therefore, if you are using geemap with Google Colab, you should use [`import geemap.eefolium`](https://github.com/giswqs/geemap/blob/master/geemap/eefolium.py). If you are using geemap with [binder](https://mybinder.org/) or a local Jupyter notebook server, you can use [`import geemap`](https://github.com/giswqs/geemap/blob/master/geemap/geemap.py), which provides more functionalities for capturing user input (e.g., mouse-clicking and moving).
"""

# %%
# Installs geemap package
import subprocess

try:
    import geemap
except ImportError:
    print('geemap package not installed. Installing ...')
    subprocess.check_call(["python", '-m', 'pip', 'install', 'geemap'])

# Checks whether this notebook is running on Google Colab
try:
    import google.colab
    import geemap.eefolium as emap
except:
    import geemap as emap

# Authenticates and initializes Earth Engine
import ee

try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()  

# %%
"""
## Create an interactive map 
The default basemap is `Google Satellite`. [Additional basemaps](https://github.com/giswqs/geemap/blob/master/geemap/geemap.py#L13) can be added using the `Map.add_basemap()` function. 
"""

# %%
Map = emap.Map(center=[40,-100], zoom=4)
# Map.add_basemap('ROADMAP') # Add Google Map
Map

# %%
"""
## Add Earth Engine Python script 
"""

# %%
# Add Earth Engine dataset
L8T1 = 'LANDSAT/LC08/C01/T1_SR'
MODIS = 'MODIS/006/MOD09GA'
S2 = 'COPERNICUS/S2_SR'

#########################/
#set date range
starta = '2019-03-01'
enda = '2019-11-30'

# Create a geodesic polygon containing Boulder, CO
reqGeometry = ee.Geometry.Polygon([
  [[43.36666667, 16.13333333], [45.91666667, 16.13333333], [45.91666667, 15.73333333], [43.36666667, 15.73333333], [43.36666667, 16.13333333]]])
# Display the polygon on the map
Map.centerObject(reqGeometry)
Map.addLayer(reqGeometry, {'color': 'FF0000'}, 'geodesic polygon')

#/Make date sequence of 15 days
start = ee.Date.fromYMD(2019,3,01)
#change the second number to how many 15 dqay sequences fit into your date range - this will provide an error if there are too many.
months = ee.List.sequence(0, 18*15, 15)

def func_rlp(d):
  return start.advance(d, 'days')

startDates = months.map(func_rlp)




#/get the date range
def getDate(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start, end)
  #sentime = ee.ImageCollection(S2)
    #.filterDate(date_range)
  return(date_range)


#get the date range for each time period for labelling.
def newDate(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start, end)
  #newa = ee.Date(date_range).get('system:time_start')
  #return(m.addBands(end))
  return(end)



list_dates = startDates.map(newDate)
print('date', list_dates)
###
#/ Add in cloud masks


##########
#S2 CLoud mask

# Bits 10 and 11 are clouds and cirrus, respectively.
cloudBitMask = ee.Number(2).pow(10).int()
cirrusBitMask = ee.Number(2).pow(11).int()

def maskS2clouds(image):
  qa = image.select('QA60')
  # Both flags should be set to zero, indicating clear conditions.
  mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
             qa.bitwiseAnd(cirrusBitMask).eq(0))
  return image.updateMask(mask)


S2QAmasked = ee.ImageCollection(S2) \
          .filter(ee.Filter.date(starta,enda)) \
          .filterBounds(reqGeometry) \
          .map(maskS2clouds)

def func_lhp(image)return image.clip(reqGeometry)};: \
          .map(function(image){return image.clip(reqGeometry)} \
          .map(func_lhp)

print("S2test", S2QAmasked)



####################
# L8 Cloud Mask

# This example demonstrates the use of the pixel QA band to mask
# clouds in surface reflectance (SR) data.  It is suitable
# for use with any of the Landsat SR datasets.

# Function to cloud mask from the pixel_qa band of Landsat 8 SR data.
def maskL8sr(image):
  # Bits 3 and 5 are cloud shadow and cloud, respectively.
  cloudShadowBitMask = 1 << 3
  cloudsBitMask = 1 << 5

  # Get the pixel QA band.
  qa = image.select('pixel_qa')

  # Both flags should be set to zero, indicating clear conditions.
  mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) \
      .And(qa.bitwiseAnd(cloudsBitMask).eq(0))

  # Return the masked image, scaled to reflectance, without the QA bands.
  return image.updateMask(mask).divide(10000) \
      .select("B[0-9]*") \
      .copyProperties(image, ["system:time_start"])


L8QAmasked = ee.ImageCollection(L8T1) \
          .filter(ee.Filter.date(starta,enda)) \
          .filterBounds(reqGeometry) \
          .map(maskL8sr)

def func_kvz(image)return image.clip(reqGeometry)};: \
          .map(function(image){return image.clip(reqGeometry)} \
          .map(func_kvz)

print("L8QAmasked", L8QAmasked)



####################
#functions

#rename sentinel-2 bands
def renamebandsS2(image):
  return image.select(['B4', 'B8', 'B11'],['bandred', 'bandNIR', 'bandMIR'])


#rename landsat-8 bands
def renamebandsL8(image):
  return image.select(['B4', 'B5', 'B6'],['bandred', 'bandNIR', 'bandMIR'])


#/can't remember what this si doing
replacement = 0

def conditional(image):
  return image.where(image.lt(0), replacement)


#convert to float
def typeconv(image):
  return image.float()


#rename MODIS bands to match those of S2 and L8
def renamebandsMODIS(image):
  return image.select(['sur_refl_b01', 'sur_refl_b02', 'sur_refl_b06'],['bandred', 'bandNIR', 'bandMIR'])


#function to calculate NDVI
def addNDVI(image):
  ndvi = image.normalizedDifference(['bandNIR', 'bandred']).rename('NDVI')
  return image.addBands(ndvi)



#function to create an rgb image
def imagergb(image):
  imagergb = image.visualize(**{'bands': ['bandred', 'bandNIR', 'bandMIR']})
  return image.addBands(imagergb)


#function to convert RGB to HSV
def hsv (image):
  rgb = image.select('vis-red', 'vis-green', 'vis-blue').float()
  huesat = rgb.divide(255).rgbToHsv().select('hue', 'saturation', 'value')
  return image.addBands(huesat)


def threshold(image):
  evi = image.expression('82 - (NDVI*250)', {
      'NDVI': image.select('NDVI')})
  a = image.select('hue')
  thres  = a.gte(evi).rename('thres')
  return image.addBands(thres)


################################
###import each data type

#import S2
S2coll = ee.ImageCollection(S2QAmasked) \
                .filter(ee.Filter.date(starta,enda)) \
                .filterBounds(reqGeometry) \
                .map(renamebandsS2)

def func_hts(image)return image.clip(reqGeometry)};: \
                .map(function(image){return image.clip(reqGeometry)} \
                .map(func_hts)

print("S2", S2coll)

#plot the firest image red band to check.
#Map.addLayer((S2coll.first()), {
#  bands:['bandred'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 9000,
#}, "TEST")


#import L8
L8tier1coll = ee.ImageCollection(L8QAmasked) \
                .filter(ee.Filter.date(starta,enda)) \
                .filterBounds(reqGeometry) \
                .map(renamebandsL8) \
                .map(conditional) \
                .map(typeconv)

def func_osf(image)return image.clip(reqGeometry)};: \
                .map(function(image){return image.clip(reqGeometry)} \
                .map(func_osf)

print("l8tier1", L8tier1coll)

#import MODIS
MODIScoll = ee.ImageCollection(MODIS) \
                .filter(ee.Filter.date(starta,enda)) \
                .filterBounds(reqGeometry) \
                .map(renamebandsMODIS)

def func_xkn(image)return image.clip(reqGeometry)};: \
                .map(function(image){return image.clip(reqGeometry)} \
                .map(func_xkn)

print("MODIS", MODIScoll)

##resample

SinImg = L8tier1coll.first().select(2)
LandsatProj = SinImg.projection()
print('Landsat projection:', LandsatProj)

#Map.addLayer(SinImg)
#resample function to the resolution and crs of Landsat
def resample (image):
  resampleImage = image \
    .reduceResolution({
      'reducer': ee.Reducer.mean(),
      'maxPixels':3000
    }) \
    .reproject({
      'crs': LandsatProj
      #scale: (-32767, 32767)
    })
  return image.addBands(resampleImage)


#/select and rename bands which have been resampled
def selectresample(image):
  return image.select(['bandred_1', 'bandNIR_1', 'bandMIR_1'],['bandred', 'bandNIR', 'bandMIR'])


#/resmaple S2 using above functions
S2resample = S2coll \
  .map(resample) \
  .map(selectresample)
print("S2resample", S2resample)

#/plot resampled S2 to check -- red band
#Map.addLayer((S2resample.median()), {
#  bands:['bandred'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 3000,
#}, "TEST")

#resmaple L8 to L8 (for consistency - probably to required)
L8resample = L8tier1coll \
  .map(resample) \
  .map(selectresample)
print("thres", L8resample)

#plot resampled L8 to check - red band
#Map.addLayer((L8resample.first()), {
#  bands:['bandred'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 3000,
#}, "TESTL8")


# merge L8 tier1 and tier2
S2L8_TS = L8resample.merge(S2resample)

#sort by time
S2L8TS = S2L8_TS.sort("system:time_start")
print("L8S2", S2L8TS)


def addTime(image):
  return image.addBands(image.metadata('system:time_start'))


###########################/
#modis
# get minimum value for each band - reduce influence of clouds
def MODIS_loc(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start,end)
  sentime = ee.ImageCollection(MODIScoll) \
    .filterDate(date_range) \
    .map(addTime)
  return(sentime.min())


#create collection of MODIS bands
list_MODISloc = startDates.map(MODIS_loc)
MODISlocs = ee.ImageCollection(list_MODISloc)
print('MODISlocs', MODISlocs)

#calculate hue, NDVI and treshold for MODIS
huemodis = MODISlocs \
  .map(imagergb) \
  .map(hsv) \
  .map(addNDVI) \
  .map(threshold)
print("thresMODIS", huemodis)

#Map.addLayer((huemodis.first()), {
#  bands:['thres'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 1,
#}, "NDVI_MODIS")

##############################
#landsat8
# get minimum value for each band - reduce influence of clouds
def L8_loc(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start,end)
  sentime = ee.ImageCollection(L8resample) \
    .filterDate(date_range)
  return(sentime.min())


#create collection of L8 bands
list_L8loc = startDates.map(L8_loc)
L8locs = ee.ImageCollection(list_L8loc)

#calculate hue, NDVI and treshold for L8
hueL8 = L8locs \
  .map(imagergb) \
  .map(hsv) \
  .map(addNDVI) \
  .map(threshold)
print("thresL8", hueL8)

#Map.addLayer((hueL8.max()), {
#  bands:['thres'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 1,
#}, "NDVI_L8")

#############################
#Sentinel2
# get minimum value for each band - reduce influence of clouds
def S2_loc(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start,end)
  sentime = ee.ImageCollection(S2resample) \
    .filterDate(date_range)
  return(sentime.min()).toFloat()


#create collection of S2 bands
list_S2loc = startDates.map(S2_loc)
S2loc = ee.ImageCollection(list_S2loc)
print('S2loc', S2loc)

#calculate hue, NDVI and treshold for S2
hueS2 = S2loc \
  .map(imagergb) \
  .map(addNDVI) \
  .map(hsv) \
  .map(threshold)
print("thresS2", hueS2)

#Map.addLayer((hueS2.first()), {
#  bands:['thres'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 1,
#}, "NDVI_S2")

###/
#MIXED S2 and L8
def mixed(m):
  start = ee.Date(m)
  end = ee.Date(m).advance(15, 'days')
  date_range = ee.DateRange(start,end)
  sentime = ee.ImageCollection(S2L8TS) \
    .filterDate(date_range)
  return(sentime.min())


#create collection of L8/S2 bands
list_mix = startDates.map(mixed)
mixloc = ee.ImageCollection(list_mix)
print("mixloc", mixloc)

#select threshold band
def selectthres(image):
  return image.select(['thres'])


#calculate hue, NDVI and treshold for mixed
huemix = mixloc \
  .map(imagergb) \
  .map(hsv) \
  .map(addNDVI) \
  .map(threshold) \
  .map(selectthres)
print("thresmix", huemix)

#Map.addLayer((huemix.first()), {
#  bands:['thres'],
#  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
#  min:0, max: 1,
#}, "NDVI_mix")

####/

def func_ysz(img):
#    img_id = img.id()
#    return img.set('id',img_id)
#
#Collection = huemix.map(func_ysz
);#end of map function


);#end of map function


names = ee.List(huemix.aggregate_array('system:index'))
print('names', names)


# Filter data
datain_t1 = huemix

def func_wfo(img):
    return img.addBands(ee.Image.constant(0).uint8().rename('counter')) \
  .select("thres").map(func_wfo) \
  .sort('system:time_start')
print('timeseries', datain_t)

datain_t = ee.ImageCollection(datain_t1) \
                .map(typeconv)
print('d', datain_t)

countThresh = 0; # mm

#function drySpells(img, list){
  # get previous image
#  prev = ee.Image(ee.List(list).get(-1))
  # find areas gt precipitation threshold (gt==0, lt==1)
#  dry = img.select('thres').gt(countThresh)
  # add previous day counter to today's counter
#  accum = prev.select('counter').add(dry).rename('counter')
  # create a result image for iteration
  # precip < thresh will equall the accumulation of counters
  # otherwise it will equal zero
#  out = img.select('thres').addBands(
        #img.select('counter').where(dry.eq(1),accum)
   #     img.select('counter').where(accum)
  #    ).float()
  #selectThres = img.select('thres')
 # testAdd = img.select('thres')
#  test2 = testAdd.add(out)
 # return ee.List(list).add(test2)
#}

def drySpells(img, list):
  # get previous image
  prev = ee.Image(ee.List(list).get(-1))
  # find areas gt precipitation threshold (gt==0, lt==1)
  dry = img.select('thres').gt(countThresh)
  # add previous day counter to today's counter
  test = img.unmask(0)
  ##UNCOMMENT NEXT LINE IF THIS TEST DOESNT WORK
  #accum = prev.select('counter').add(img.select('thres')).rename('counter')
  accum = prev.select('counter').add(test.select('thres')).rename('counter')
  # create a result image for iteration
  # precip < thresh will equall the accumulation of counters
  # otherwise it will equal zero
  out = img.select('thres') \
        .addBands(accum)
        #img.select('counter').where(dry.eq(1),accum) \
      .float()
  #selectThres = img.select('thres')
  #testAdd = img.select('thres')
  #test2 = testAdd.add(out)
  return ee.List(list).add(out)



dataset = datain_t \
.sort('system:time_start:', False)
print(dataset,"dataset")

# create first image for iteration
first = ee.List([ee.Image(dataset.first())])

# apply dry speall iteration function - this one to get final accumulation
#maxDrySpell = ee.ImageCollection.fromImages(
#    dataset.iterate(drySpells,first)
#).max().select('counter'); # get the max value

#apply dry speall iteration function
maxDrySpell = ee.ImageCollection.fromImages(
    dataset.iterate(drySpells,first)
).select('counter', 'thres').filterBounds(reqGeometry); # get the max value
print("countmixed", maxDrySpell)


# display results
Map.addLayer(maxDrySpell.select('counter'),{'min':0, 'max':10, 'palette':'#9ecae1,#ffffff,#ffeda0,#feb24c,#f03b20'},'Max Dry Spells')

fromList = ee.FeatureCollection(maxDrySpell)
#fromList = ee.FeatureCollection(huemix)
print('fromList', fromList)




#add date
def dateMapFunction(i):
  img = ee.Image(ee.List(i).get(0))
  date = ee.Date(ee.List(i).get(1))
  newImage = img.set('enddate', date)
  return newImage


withDates = fromList.toList(100).zip(list_dates)
print("pairs", withDates)

newfeature = withDates.map(dateMapFunction)
print("withdate", newfeature)

dateAdd = ee.ImageCollection(newfeature) \
                .map(typeconv)
print('dadd', dateAdd)

Map.addLayer((dateAdd.first()), {
  'bands':['thres'],
  'palette': ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
  'min':0, 'max': 1,
}, "NDVI_mix")

print('tohere')
print

#/export NDWI
sizeNDWI = dateAdd.size().getInfo()
NDWIlist = dateAdd.toList(sizeNDWI)

print('testing', NDWIlist)

for n in range(n=0, n<sizeNDWI, 1):
  imageNDWI = ee.Image(NDWIlist.get(n))
  dateNDWI = ee.Date(imageNDWI.get('enddate')).format('yyyyMMdd')
  dateNDWI = dateNDWI.getInfo()
  nameNDWI = dateNDWI +'_locusts_'
  Export.image.toDrive({
    'image': imageNDWI,
    'description': nameNDWI,
    'fileNamePrefix': nameNDWI, # this is the name actually
    'folder': 'GEE Locusts',
    'scale': 90,
    'region': reqGeometry,
  })






# %%
"""
## Display Earth Engine data layers 
"""

# %%
Map.addLayerControl() # This line is not needed for ipyleaflet-based Map.
Map