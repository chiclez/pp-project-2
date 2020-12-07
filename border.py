import pandas as pd
import math
from geopy.distance import geodesic
from geopy.point import Point as Point
from shapely import geometry
import os

def CalculateMidpoint():

    '''
    This midpoint formula will calculate the midpoint of the Scottish border
    using the equation found at http://www.movable-type.co.uk/scripts/latlong.html
    This function uses the Point function from geopy

    Input: None

    Output: 
    midPoint: a tupple containing the midpoint of the border. 
    '''

    borderWest = (54.995769, -3.052872)
    borderEast = (55.806881, -2.042987)

    # Convert the coordinates to radians
    borderWestLat, borderWestLon = math.radians(borderWest[0]), math.radians(borderWest[1])
    borderEastLat, borderEastLon = math.radians(borderEast[0]), math.radians(borderEast[1])

    # Follow the equations found at http://www.movable-type.co.uk/scripts/latlong.html
    # Constants
    deltaLon = borderEastLon - borderWestLon
    bx = math.cos(borderEastLat) * math.cos(deltaLon)
    by = math.cos(borderEastLat) * math.sin(deltaLon)
    
    # Coordinates of the midpoint
    midLat = math.atan2(math.sin(borderWestLat) + math.sin(borderEastLat),
        math.sqrt(((math.cos(borderWestLat) + bx) ** 2 + by ** 2)))
    midLon = borderWestLon + math.atan2(by, math.cos(borderWestLat) + bx)
    
    # Normalise the longitude to a −180 … +180 range
    midLon = (midLon + 3 * math.pi) % (2 * math.pi) - math.pi

    # Convert back to degrees
    midLat = math.degrees(midLat)
    midLon = math.degrees(midLon)

    # Calculate the midpoint using the Point geopy function
    midpoint = Point(latitude = midLat, longitude=midLon)

    return midpoint

def GetDistance(keyPlace, roadpoint):
    '''
    This mini-script will be used for calculating the geodesic distance between
    two places, a key place and the road point, using the geodesic function of 
    geopy. This is an approximation of a distance.

    Inputs:
    row: pandas dataframe containing the datapoints

    Output:
    calculatedDistance = Geodesic distance (in km) rounded to 2 decimals

    '''

    # Set the coordinates as tupples
    roadPoint = (roadpoint['latitude'], roadpoint['longitude'])

    calculatedDistance = round(geodesic(keyPlace, roadPoint).kilometers,2)

    return calculatedDistance

def PolygonBorder(polygon, roadpoint):
    '''
    This mini-script will be used for calculating the geodesic distance between
    two places, a key place and the road point, using the geodesic function of 
    geopy. This is an approximation of a distance.

    Inputs:
    roadpoint: pandas dataframe containing the datapoints

    Output:
    roadpointBorder = A boolean value that will determine whether the roadpoint 
    is found in the defined polygon

    '''

    # Set the coordinates as tupples
    roadPoint = geometry.Point(roadpoint['latitude'], roadpoint['longitude'])
    roadpointBorder = roadPoint.within(polygon)

    return roadpointBorder

def LoadData():

    '''
    This function loads the DFT dataset csv file as a pandas dataframe. It will
    process the dataframeand convert columns to a suitable format for data analysis

    Input: None
    Output: rawData (DFT dataframe) 
    '''

     # Import the csv parsing dates and setting the junction road names columns as strings.
    rawData = pd.read_csv("dft_rawcount_region_id_3.csv", parse_dates = ["count_date"], 
                          dtype={'start_junction_road_name': str, 'end_junction_road_name': str})

    rawData["count_date"] = pd.to_datetime(rawData["count_date"], yearfirst = True, infer_datetime_format= True)

    return rawData

def FindBikesMidpoint():

    '''
    This function will locate the bicycles found on a 10 km distance to the Anglo
    Scottish border using a midpoint approach. The midpoint is calculated by using
    the far east and far west coordinates of the border.

    Input: None

    Output
    bikesOnBorders: a pandas dataframe with the roadpoint, coordinates, distance
    to the border and number of bikes found across the whole DFT dataset
    '''

    #Load the DFT data
    rawData = LoadData()

    # Select data only from the Scottish borders county and only with pedal_cycles
    borderData = rawData.loc[(rawData["local_authority_name"] == "Scottish Borders")
                             & (rawData["pedal_cycles"] > 0)]

    # The maximum distance to find a roadpoint from the midpoint is 10 km
    distance = 10

    # Get the midpoint and cast the coordinates in tupple form
    midpoint = CalculateMidpoint()
    midpointCoordinates = (midpoint.latitude, midpoint.longitude)

    # Prepare a copy of the original dataframe for calculating the distances
    bikesOnBorders = borderData.copy()

    # Find the geodesic distance to the midpoint
    bikesOnBorders["distance_to_border"] = borderData.apply(lambda row: GetDistance(midpointCoordinates, row), axis=1)

    # Create a new dataframe by selecting only the required information from the original dataframe
    bikesOnBorders = bikesOnBorders[["year", "count_point_id", "road_type","road_name", 
                                  "latitude", "longitude", "pedal_cycles", "distance_to_border"]]

    # Select only the roadpoints within the allowed distance and sort by year
    bikesOnBorders = bikesOnBorders.loc[(bikesOnBorders["distance_to_border"] <= distance)]
    bikesOnBorders = bikesOnBorders.sort_values(by=["year"], ascending = True)

    return bikesOnBorders

def FindBikesInterval():

    '''
    This function will locate the bicycles found on a 555 m distance to the Anglo
    Scottish border using an interval approach done on the latitude or the longitude
    from every major crossing point. 

    Input: None

    Output
    bikesOnBorders: a pandas dataframe with the roadpoint, coordinates, distance
    to the border and number of bikes found across the whole DFT dataset
    '''

    #Load the DFT data
    rawData = LoadData()

    # Select data only from the Scottish borders county and only with pedal_cycles
    borderData = rawData.loc[(rawData["local_authority_name"] == "Scottish Borders")
                             & (rawData["pedal_cycles"] > 0)]

    # Border crossing coordinates
    borderWest = (54.995769, -3.052872)
    borderEast = (55.806881, -2.042987)
    carlisleCross = (55.049714, -2.960520)
    ladykirkCross = (55.718895, -2.177002)
    deadwaterCross = (55.355528, -2.481019)
    kelsoCross = (55.566299, -2.263140)
    jedburghCross = (55.354486, -2.478119)
    coldstreamCross = (55.654783, -2.242233)

    # Set an border interval of 0.005 degrees (equivalent to 555 m)
    interval = 0.005

    # Filter the roadpoints within the border area in latitude: border + interval
    # or in longitude: border - interval (where the border crossing is West to East)
    bikesOnBorders = borderData.loc[((borderData["latitude"] >= borderWest[0]) &
                                     (borderData["latitude"] <= borderWest[0] + interval)) | 
                                     ((borderData["latitude"] >= jedburghCross[0]) &
                                     (borderData["latitude"] <= jedburghCross[0] + interval)) |
                                     ((borderData["latitude"] >= carlisleCross[0]) &
                                     (borderData["latitude"] <= carlisleCross[0] + interval)) |
                                     ((borderData["latitude"] >= kelsoCross[0]) &
                                     (borderData["latitude"] <= kelsoCross[0] - interval)) |
                                     ((borderData["latitude"] >= deadwaterCross[0]) &
                                     (borderData["latitude"] <= deadwaterCross[0] + interval)) |
                                     ((borderData["latitude"] >= borderEast[0]) &
                                     (borderData["latitude"] <= borderEast[0] + interval)) |
                                     ((borderData["longitude"] >= jedburghCross[1]) &
                                     (borderData["longitude"] <= jedburghCross[1] - interval)) |
                                     ((borderData["longitude"] >= coldstreamCross[1]) &
                                     (borderData["longitude"] <= coldstreamCross[1] - interval))]

    # Create a new dataframe by selecting only the required information from the original dataframe
    bikesOnBorders = bikesOnBorders[["year", "count_point_id", "road_type","road_name", 
                                  "latitude", "longitude", "pedal_cycles"]]
    bikesOnBorders = bikesOnBorders.sort_values(by=["year"], ascending = True)

    return bikesOnBorders

def FindBikesPolygon():

    '''
    This function will locate the bicycles found on a 555 m distance to the Anglo
    Scottish border using 2 Shapely polygons: One polygon for the east border and
    one for the west-central border.

    Input: None

    Output
    bikesOnBorders: a pandas dataframe with the roadpoint, coordinates, distance
    to the border and number of bikes found across the whole DFT dataset
    '''

    #Load the DFT data
    rawData = LoadData()

    # Select data only from the Scottish borders county and only with pedal_cycles
    borderData = rawData.loc[(rawData["local_authority_name"] == "Scottish Borders")
                             & (rawData["pedal_cycles"] > 0)]

    # Border crossing coordinates
    borderWest = (54.995769, -3.052872)
    borderEast = (55.806881, -2.042987)
    borderCarham = (55.63214657346817, -2.336614595368269)
    borderCheviot = (55.35494550715024, -2.4775857685793206)
    borderShotton = (55.56652764514263, -2.263512214239654)

    # Set an border boundary of 0.005 degrees (equivalent to 555 m)
    boundary = 0.005

    # Create a Polygon
    coordsEast = [borderCarham, (borderCarham[0]+ boundary, borderCarham[1]), borderEast, (borderEast[0]+ boundary, borderEast[1])]
    coordsWest = [borderWest, (borderWest[0]+ boundary, borderWest[1]), borderCheviot, (borderCheviot[0]+ boundary, borderCheviot[1])]
    polygonEast = geometry.Polygon(coordsEast)
    polygonWest = geometry.Polygon(coordsWest)

    # Find if the roadpoints are within the polygons
    bikesOnBorders = borderData.copy()
    bikesOnBorders["roadpoint_east_border"] = borderData.apply(lambda row: PolygonBorder(polygonEast, row), axis=1)
    bikesOnBorders["roadpoint_west_border"] = borderData.apply(lambda row: PolygonBorder(polygonWest, row), axis=1)

    bikesOnBorders = bikesOnBorders.loc[(bikesOnBorders["roadpoint_west_border"] == True) |
                                        (bikesOnBorders["roadpoint_east_border"] == True)]

    # Create a new dataframe by selecting only the required information from the original dataframe
    bikesOnBorders = bikesOnBorders[["year", "count_point_id", "road_type","road_name", 
                                  "latitude", "longitude", "pedal_cycles", 
                                  "roadpoint_east_border", "roadpoint_west_border"]]
    bikesOnBorders = bikesOnBorders.sort_values(by=["year"], ascending = True)

    return bikesOnBorders