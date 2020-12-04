import pandas as pd
import numpy as np
import seaborn
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import time
import os
import scipy as sc

def FindTraffic(city, year):
    '''
    This script will be used for finding patterns between the traffic and key 
    places (i.e. Hospitals, schools, supermarkets) in the top 5 most populated 
    cities of Scotland: Glasgow, Edinburgh, Aberdeen, Perth and Dundee
    
    Inputs:
    City: Enter the local authority name, i.e. for Edinburgh use City of Edinburgh
    year: Select a year between 2000 and 2019

    Output:

    '''

    rawData = pd.read_csv("dft_rawcount_region_id_3.csv", parse_dates = ["year"], 
                          dtype={'start_junction_road_name': str,
                                 'end_junction_road_name': str})
    rawData.rename(columns = {"year":"date"}, inplace = True)
    rawData["date"] = pd.to_datetime(rawData["date"], yearfirst = True, 
                      infer_datetime_format= True)

    rawData["year"] = pd.to_datetime(rawData["date"], yearfirst = True).dt.year

    # Select data considering a specific city and a specific year
    cityData = rawData.loc[(rawData["local_authority_name"] == city) 
                       & (rawData["year"] == year)]
         
    # Group the roads and find the (straight-line) distance to a key place
    cityRoads = pd.DataFrame({'count': cityData.groupby(["road_name","road_type",
                          "latitude","longitude","all_motor_vehicles"]).size()}).reset_index()

    cityRoads['distance'] = cityRoads.apply(lambda row: GetDistance(row),axis=1)

    return cityRoads.head() #Placeholder for having something to return

def GetDistance(spot, roadpoint):
    '''
    This mini-script will be used for calculating the geodesic distance between
    two places, a key place and the road point, using the geodesic function of 
    geopy. This is an approximation of a distance.

    Inputs:
    row: pandas dataframe containing the datapoints

    Output:
    calculatedDistance = Geodesic distance (in km) rounded to 2 decimals

    '''
    key = spot
    roadPoint = (roadpoint['latitude'], roadpoint['longitude'])

    calculatedDistance = round(geodesic(key, roadPoint).kilometers,2)

    return calculatedDistance

def LoadData():

    rawData = pd.read_csv("dft_rawcount_region_id_3.csv", parse_dates = ["year"], 
                          dtype={'start_junction_road_name': str,
                                 'end_junction_road_name': str})
    rawData.rename(columns = {"year":"date"}, inplace = True)
    rawData["date"] = pd.to_datetime(rawData["date"], yearfirst = True, 
                      infer_datetime_format= True)

    rawData["year"] = pd.to_datetime(rawData["date"], yearfirst = True).dt.year

    return rawData

def LocateBorder():

    eastPoint = (a,b)
    westPoint = (c,d)
    midPoint = (e, f)

    return