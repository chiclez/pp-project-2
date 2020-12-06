import pandas as pd
import math
from geopy.distance import geodesic
from geopy.point import Point as Point
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

    #borderWest = [55.0, -3.0]
    #borderEast = [55.81, -2.03]
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

def LoadData():

    '''
    This function loads the DFT dataset csv file as a pandas dataframe. It will
    process the dataframeand convert columns to a suitable format for data analysis

    Input: None
    Output: rawData (DFT dataframe) 
    '''

     # Import the csv parsing dates and setting the junction road names columns 
     # as strings.
    rawData = pd.read_csv("dft_rawcount_region_id_3.csv", parse_dates = ["count_date"], 
                          dtype={'start_junction_road_name': str, 'end_junction_road_name': str})

    rawData["count_date"] = pd.to_datetime(rawData["count_date"], yearfirst = True, infer_datetime_format= True)

    return rawData

def ScottishBorders(rawData):

    '''
    This function will call the DFT dataframe and will process only the Scottish
    borders county. Scottish Borders comprises: Berwickshire, Peeblesshire, 
    Roxburghshire, and Selkirkshire

    Input
    rawData: DFT dataframe

    Output
    borderRoads: Filtered dataset containing the data for the Scottish Borders
    
    '''

    # Select data considering the border
    borderRoads = rawData.loc[(rawData["local_authority_name"] == "Scottish Borders")]
         
    # Group the roads
    borderRoads = pd.DataFrame({'count': borderRoads.groupby(["year", "count_point_id", 
                               "road_type","road_name", "latitude", "longitude", 
                               "pedal_cycles"]).size()}).reset_index()

    return borderRoads

def LocateBikesBorders():

    rawData = LoadData()
    borderData = ScottishBorders(rawData)
    borderData = borderData.loc[(borderData["pedal_cycles"] > 0)]

    # The maximum distance to find a roadpoint from the midpoint is 10 km
    distance = 10

    # Get the midpoint and cast the coordinates in tupple form
    midpoint = CalculateMidpoint()
    midpointCoordinates = (midpoint.latitude, midpoint.longitude)

    # Find the geodesic distance to the midpoint
    borderData["distance_to_border"] = borderData.apply(lambda row: GetDistance(midpoint, row), axis=1)

    # Select only the roadpoints within the allowed distance
    bikesOnBorders = borderData.loc[(borderData["distance_to_border"] <= distance)]
    bikesOnBorders = bikesOnBorders.drop(columns = ["count"])
    bikesOnBorders = bikesOnBorders.sort_values(by=["year"], ascending = True)

    return bikesOnBorders

def LocateBikesBordersInterval():

    # STILL  INCOMPLETE
    rawData = LoadData()
    borderData = ScottishBorders(rawData)
    borderData = borderData.loc[(borderData["pedal_cycles"] > 0)]

    distance = 10

    borderWest = [54.995769, -3.052872]
    borderEast = [55.806881, -2.042987]

    interval = 0.1

    newBorderW = [borderWest[0]+interval, borderWest[1]]

    midPoint = Midpoint()
    middlePoint = (midPoint.latitude, midPoint.longitude)

    # Find the geodesic distance to a the midpoint
    borderData["distance_to_border"] = borderData.apply(lambda row: GetDistance(middlePoint, row), axis=1)

    # Select only the roadpoints within the allowed distance
    bikesOnBorders = borderData.loc[(borderData["distance_to_border"] <= distance)]
    bikesOnBorders = bikesOnBorders.drop(columns = ["count"])

    bikesOnBorders = bikesOnBorders.sort_values(by=["year"], ascending = True)

    return bikesOnBorders

a = LocateBikesBorders()
print(a)