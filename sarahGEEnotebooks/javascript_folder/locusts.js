
L8T1 = 'LANDSAT/LC08/C01/T1_SR'
MODIS = 'MODIS/006/MOD09GA'
S2 = 'COPERNICUS/S2_SR'

///////////////////////////////////////////////////
//set date range
var starta = '2019-03-01';
var enda = '2019-11-30';

// Create a geodesic polygon containing Boulder, CO
var reqGeometry = ee.Geometry.Polygon([
  [[43.36666667, 16.13333333], [45.91666667, 16.13333333], [45.91666667, 15.73333333], [43.36666667, 15.73333333], [43.36666667, 16.13333333]]]);
// Display the polygon on the map
Map.centerObject(reqGeometry);
Map.addLayer(reqGeometry, {color: 'FF0000'}, 'geodesic polygon');

///Make date sequence of 15 days
var start = ee.Date.fromYMD(2019,3,01);
//change the second number to how many 15 dqay sequences fit into your date range - this will provide an error if there are too many.
var months = ee.List.sequence(0, 18*15, 15);   
var startDates = months.map(function(d) {
  return start.advance(d, 'days');   
});

///get the date range
var getDate = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start, end)
  //var sentime = ee.ImageCollection(S2)   
    //.filterDate(date_range);
  return(date_range); 
};   

//get the date range for each time period for labelling.
var newDate = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start, end)
  //var newa = ee.Date(date_range).get('system:time_start');
  //return(m.addBands(end));
  return(end)
};


var list_dates = startDates.map(newDate)
print('date', list_dates)
//////
/// Add in cloud masks


////////////////////
//S2 CLoud mask

// Bits 10 and 11 are clouds and cirrus, respectively.
var cloudBitMask = ee.Number(2).pow(10).int();
var cirrusBitMask = ee.Number(2).pow(11).int();

function maskS2clouds(image) {
  var qa = image.select('QA60');
  // Both flags should be set to zero, indicating clear conditions.
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(
             qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask);
}

var S2QAmasked = ee.ImageCollection(S2)
          .filter(ee.Filter.date(starta,enda))
          .filterBounds(reqGeometry)
          .map(maskS2clouds)
          .map(function(image){return image.clip(reqGeometry)});
print("S2test", S2QAmasked)



////////////////////////////////////////
// L8 Cloud Mask

// This example demonstrates the use of the pixel QA band to mask
// clouds in surface reflectance (SR) data.  It is suitable
// for use with any of the Landsat SR datasets.

// Function to cloud mask from the pixel_qa band of Landsat 8 SR data.
function maskL8sr(image) {
  // Bits 3 and 5 are cloud shadow and cloud, respectively.
  var cloudShadowBitMask = 1 << 3;
  var cloudsBitMask = 1 << 5;

  // Get the pixel QA band.
  var qa = image.select('pixel_qa');

  // Both flags should be set to zero, indicating clear conditions.
  var mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
      .and(qa.bitwiseAnd(cloudsBitMask).eq(0));

  // Return the masked image, scaled to reflectance, without the QA bands.
  return image.updateMask(mask).divide(10000)
      .select("B[0-9]*")
      .copyProperties(image, ["system:time_start"]);
}

var L8QAmasked = ee.ImageCollection(L8T1)
          .filter(ee.Filter.date(starta,enda))
          .filterBounds(reqGeometry)
          .map(maskL8sr)
          .map(function(image){return image.clip(reqGeometry)});
print("L8QAmasked", L8QAmasked);



////////////////////////////////////////
//functions

//rename sentinel-2 bands
var renamebandsS2 = function(image){
  return image.select(['B4', 'B8', 'B11'],['bandred', 'bandNIR', 'bandMIR']);
};

//rename landsat-8 bands
var renamebandsL8 = function(image){
  return image.select(['B4', 'B5', 'B6'],['bandred', 'bandNIR', 'bandMIR']);
};

///can't remember what this si doing
var replacement = 0

var conditional = function(image) {
  return image.where(image.lt(0), replacement);
};

//convert to float
var typeconv = function(image) {
  return image.float();
};

//rename MODIS bands to match those of S2 and L8
var renamebandsMODIS = function(image){
  return image.select(['sur_refl_b01', 'sur_refl_b02', 'sur_refl_b06'],['bandred', 'bandNIR', 'bandMIR']);
};

//function to calculate NDVI
var addNDVI = function(image) {
  var ndvi = image.normalizedDifference(['bandNIR', 'bandred']).rename('NDVI');
  return image.addBands(ndvi);
};


//function to create an rgb image
var imagergb = function(image){
  var imagergb = image.visualize({bands: ['bandred', 'bandNIR', 'bandMIR']});
  return image.addBands(imagergb);
};

//function to convert RGB to HSV
var hsv = function (image) {
  var rgb = image.select('vis-red', 'vis-green', 'vis-blue').float();
  var huesat = rgb.divide(255).rgbToHsv().select('hue', 'saturation', 'value');
  return image.addBands(huesat);
};

var threshold = function(image) {
  var evi = image.expression('82 - (NDVI*250)', {
      'NDVI': image.select('NDVI')});
  var a = image.select('hue');
  var thres  = a.gte(evi).rename('thres');
  return image.addBands(thres);
};

////////////////////////////////////////////////////////////////
//////import each data type

//import S2
var S2coll = ee.ImageCollection(S2QAmasked)
                .filter(ee.Filter.date(starta,enda))
                .filterBounds(reqGeometry)
                .map(renamebandsS2)
                .map(function(image){return image.clip(reqGeometry)});
print("S2", S2coll); 

//plot the firest image red band to check.
//Map.addLayer((S2coll.first()), {
//  bands:['bandred'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 9000,
//}, "TEST");


//import L8
var L8tier1coll = ee.ImageCollection(L8QAmasked)
                .filter(ee.Filter.date(starta,enda))
                .filterBounds(reqGeometry)
                .map(renamebandsL8)
                .map(conditional)
                .map(typeconv)
                .map(function(image){return image.clip(reqGeometry)});
print("l8tier1", L8tier1coll); 

//import MODIS
var MODIScoll = ee.ImageCollection(MODIS)
                .filter(ee.Filter.date(starta,enda))
                .filterBounds(reqGeometry)
                .map(renamebandsMODIS)
                .map(function(image){return image.clip(reqGeometry)});
print("MODIS", MODIScoll); 

////resample

var SinImg = L8tier1coll.first().select(2);
var LandsatProj = SinImg.projection();
print('Landsat projection:', LandsatProj);

//Map.addLayer(SinImg);
//resample function to the resolution and crs of Landsat
var resample = function (image) {
  var resampleImage = image
    .reduceResolution({
      reducer: ee.Reducer.mean(),
      maxPixels:3000
    })
    .reproject({
      crs: LandsatProj
      //scale: (-32767, 32767)
    });
  return image.addBands(resampleImage);
};

///select and rename bands which have been resampled
var selectresample = function(image){
  return image.select(['bandred_1', 'bandNIR_1', 'bandMIR_1'],['bandred', 'bandNIR', 'bandMIR']);
};

///resmaple S2 using above functions
var S2resample = S2coll
  .map(resample)
  .map(selectresample)
print("S2resample", S2resample);

///plot resampled S2 to check -- red band
//Map.addLayer((S2resample.median()), {
//  bands:['bandred'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 3000,
//}, "TEST");

//resmaple L8 to L8 (for consistency - probably to required)
var L8resample = L8tier1coll
  .map(resample)
  .map(selectresample)
print("thres", L8resample);

//plot resampled L8 to check - red band
//Map.addLayer((L8resample.first()), {
//  bands:['bandred'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 3000,
//}, "TESTL8");


// merge L8 tier1 and tier2
var S2L8_TS = L8resample.merge(S2resample)

//sort by time
var S2L8TS = S2L8_TS.sort("system:time_start")
print("L8S2", S2L8TS)


var addTime = function(image) {
  return image.addBands(image.metadata('system:time_start'));
};

/////////////////////////////////////////////////////// 
//modis
// get minimum value for each band - reduce influence of clouds 
var MODIS_loc = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start,end)
  var sentime = ee.ImageCollection(MODIScoll)   
    .filterDate(date_range)
    .map(addTime)
  return(sentime.min()); 
};   

//create collection of MODIS bands
var list_MODISloc = startDates.map(MODIS_loc);   
var MODISlocs = ee.ImageCollection(list_MODISloc);
print('MODISlocs', MODISlocs)

//calculate hue, NDVI and treshold for MODIS 
var huemodis = MODISlocs
  .map(imagergb)
  .map(hsv)
  .map(addNDVI)
  .map(threshold);
print("thresMODIS", huemodis);

//Map.addLayer((huemodis.first()), {
//  bands:['thres'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 1,
//}, "NDVI_MODIS");

////////////////////////////////////////////////////////////
//landsat8
// get minimum value for each band - reduce influence of clouds 
var L8_loc = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start,end)
  var sentime = ee.ImageCollection(L8resample)   
    .filterDate(date_range)   
  return(sentime.min()); 
};

//create collection of L8 bands
var list_L8loc = startDates.map(L8_loc);   
var L8locs = ee.ImageCollection(list_L8loc);   

//calculate hue, NDVI and treshold for L8
var hueL8 = L8locs
  .map(imagergb)
  .map(hsv)
  .map(addNDVI)
  .map(threshold);
print("thresL8", hueL8);

//Map.addLayer((hueL8.max()), {
//  bands:['thres'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 1,
//}, "NDVI_L8");

//////////////////////////////////////////////////////////
//Sentinel2
// get minimum value for each band - reduce influence of clouds 
var S2_loc = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start,end)
  var sentime = ee.ImageCollection(S2resample)   
    .filterDate(date_range)   
  return(sentime.min()).toFloat(); 
};   

//create collection of S2 bands
var list_S2loc = startDates.map(S2_loc);   
var S2loc = ee.ImageCollection(list_S2loc); 
print('S2loc', S2loc)

//calculate hue, NDVI and treshold for S2
var hueS2 = S2loc
  .map(imagergb)
  .map(addNDVI)
  .map(hsv)
  .map(threshold);
print("thresS2", hueS2);

//Map.addLayer((hueS2.first()), {
//  bands:['thres'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 1,
//}, "NDVI_S2");

///////
//MIXED S2 and L8
var mixed = function(m){
  var start = ee.Date(m);
  var end = ee.Date(m).advance(15, 'days');
  var date_range = ee.DateRange(start,end)
  var sentime = ee.ImageCollection(S2L8TS)   
    .filterDate(date_range);
  return(sentime.min()); 
};   

//create collection of L8/S2 bands
var list_mix = startDates.map(mixed);   
var mixloc = ee.ImageCollection(list_mix);   
print("mixloc", mixloc)

//select threshold band
var selectthres = function(image){
  return image.select(['thres']);
};

//calculate hue, NDVI and treshold for mixed
var huemix = mixloc
  .map(imagergb)
  .map(hsv)
  .map(addNDVI)
  .map(threshold)
  .map(selectthres);
print("thresmix", huemix);

//Map.addLayer((huemix.first()), {
//  bands:['thres'],
//  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
//  min:0, max: 1,
//}, "NDVI_mix");

/////////
//var Collection = huemix.map(function(img) {
//    var img_id = img.id();
//    return img.set('id',img_id);
//});//end of map function


var names = ee.List(huemix.aggregate_array('system:index'));
print('names', names)


// Filter data
var datain_t1 = huemix
  .select("thres").map(function(img){
    return img.addBands(ee.Image.constant(0).uint8().rename('counter'));
  })
  .sort('system:time_start');
print('timeseries', datain_t)

var datain_t = ee.ImageCollection(datain_t1)
                .map(typeconv)
print('d', datain_t)

var countThresh = 0; // mm

//function drySpells(img, list){
  // get previous image
//  var prev = ee.Image(ee.List(list).get(-1));
  // find areas gt precipitation threshold (gt==0, lt==1)
//  var dry = img.select('thres').gt(countThresh);
  // add previous day counter to today's counter
//  var accum = prev.select('counter').add(dry).rename('counter');
  // create a result image for iteration
  // precip < thresh will equall the accumulation of counters
  // otherwise it will equal zero
//  var out = img.select('thres').addBands(
        //img.select('counter').where(dry.eq(1),accum)
   //     img.select('counter').where(accum)
  //    ).float();
  //var selectThres = img.select('thres')
 // var testAdd = img.select('thres')
//  var test2 = testAdd.add(out)
 // return ee.List(list).add(test2);
//}

function drySpells(img, list){
  // get previous image
  var prev = ee.Image(ee.List(list).get(-1));
  // find areas gt precipitation threshold (gt==0, lt==1)
  var dry = img.select('thres').gt(countThresh);
  // add previous day counter to today's counter
  var test = img.unmask(0)
  ////UNCOMMENT NEXT LINE IF THIS TEST DOESNT WORK
  //var accum = prev.select('counter').add(img.select('thres')).rename('counter');
  var accum = prev.select('counter').add(test.select('thres')).rename('counter');
  // create a result image for iteration
  // precip < thresh will equall the accumulation of counters
  // otherwise it will equal zero
  var out = img.select('thres')
        .addBands(accum)
        //img.select('counter').where(dry.eq(1),accum)
        //img.select('counter')//.where(img.select('thres'),accum)
      .float();
  //var selectThres = img.select('thres')
  //var testAdd = img.select('thres')
  //var test2 = testAdd.add(out)
  return ee.List(list).add(out);
}


var dataset = datain_t
.sort('system:time_start:', false);
print(dataset,"dataset");

// create first image for iteration
var first = ee.List([ee.Image(dataset.first())]);

// apply dry speall iteration function - this one to get final accumulation
//var maxDrySpell = ee.ImageCollection.fromImages(
//    dataset.iterate(drySpells,first)
//).max().select('counter'); // get the max value

//apply dry speall iteration function
var maxDrySpell = ee.ImageCollection.fromImages(
    dataset.iterate(drySpells,first)
).select('counter', 'thres').filterBounds(reqGeometry); // get the max value
print("countmixed", maxDrySpell)


// display results
Map.addLayer(maxDrySpell.select('counter'),{min:0,max:10,palette:'#9ecae1,#ffffff,#ffeda0,#feb24c,#f03b20'},'Max Dry Spells');

var fromList = ee.FeatureCollection(maxDrySpell)
//var fromList = ee.FeatureCollection(huemix);
print('fromList', fromList);




//add date
var dateMapFunction = function(i) {
  var img = ee.Image(ee.List(i).get(0));
  var date = ee.Date(ee.List(i).get(1));
  var newImage = img.set('enddate', date);
  return newImage;
};

var withDates = fromList.toList(100).zip(list_dates);
print("pairs", withDates);

var newfeature = withDates.map(dateMapFunction);
print("withdate", newfeature);

var dateAdd = ee.ImageCollection(newfeature)
                .map(typeconv)
print('dadd', dateAdd)

Map.addLayer((dateAdd.first()), {
  bands:['thres'],
  palette: ['8B0000','FF0000', 'FF4500', 'FFFF00', '00FF00','008000', '006400'],
  min:0, max: 1,
}, "NDVI_mix");

print('tohere')
print

///export NDWI
var sizeNDWI = dateAdd.size().getInfo()
var NDWIlist = dateAdd.toList(sizeNDWI)

print('testing', NDWIlist)

for (var n=0; n<sizeNDWI; n++) {
  var imageNDWI = ee.Image(NDWIlist.get(n))
  var dateNDWI = ee.Date(imageNDWI.get('enddate')).format('yyyyMMdd');
  dateNDWI = dateNDWI.getInfo();
  var nameNDWI = dateNDWI +'_locusts_';
  Export.image.toDrive({
    image: imageNDWI,
    description: nameNDWI,
    fileNamePrefix: nameNDWI, // this is the name actually
    folder: 'GEE Locusts',
    scale: 90,
    region: reqGeometry,
  })
}


  