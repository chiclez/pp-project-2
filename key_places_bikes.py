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

def Hospitals():

    curDir = os.getcwd()
    hospitalCsv = os.path.join(curDir,"Hospital.csv")

    hospitalDic = pd.read_csv(hospitalCsv, dtype={"latitude": float, "longitude": float}, 
                            usecols=["city","latitude","longitude", "name"])
    return hospitalDic

def Markets():

    curDir = os.getcwd()
    marketCsv = os.path.join(curDir,"Main_markets.csv")

    marketDic = pd.read_csv(marketCsv, dtype={"latitude": float, "longitude": float}, 
                            usecols=["city","latitude","longitude", "name"])

    return marketDic

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

def CityData(rawData):

    # Select data considering the top 5 cities
    cityRoads = rawData.loc[(rawData["local_authority_name"] == "City of Edinburgh") | 
                            (rawData["local_authority_name"] == "Glasgow City") | 
                           (rawData["local_authority_name"] == "Perth & Kinross") |
                           (rawData["local_authority_name"] == "Aberdeen City") |
                           (rawData["local_authority_name"] == "Dundee City")]
         
    # Group the roads
    cityRoads = pd.DataFrame({'count': cityRoads.groupby(["count_point_id", 
                           "latitude", "longitude","pedal_cycles"]).size()}).reset_index()

    return cityRoads

def HospitalBikes():

    # Load data and select top 5 cities
    rawData = LoadData()
    cityRoads = CityData(rawData)

    # Load Hospitals data
    hospitalInfo = Hospitals()

    hospitalCoordinates = hospitalInfo[["latitude", "longitude"]]

    closest_roadpoint = []
    distance_roadpoint = []

    #t1 = time.perf_counter()

    # Find the geodesic distance to a key place
    for i in range(0, len(hospitalInfo)):
        coordinates = (hospitalCoordinates.iloc[i,0], hospitalCoordinates.iloc[i,1])
        cityRoads[f"market_{i}"] = cityRoads.apply(lambda row: GetDistance(coordinates, row), axis=1)

        minDistance = cityRoads[f"market_{i}"].min()
        idx = cityRoads[f"market_{i}"].idxmin()

        roadpoint = cityRoads.iloc[idx,0]

        closest_roadpoint.append(roadpoint)
        distance_roadpoint.append(minDistance)

    #t2 = time.perf_counter()
    #print(t2 - t1) #timer

    hospitalInfo["count_point_id"] = closest_roadpoint
    hospitalInfo["distance"] = distance_roadpoint

    bikesOnRoads = cityRoads[["count_point_id","pedal_cycles"]]

    hospitalsCycles = pd.merge(hospitalInfo, bikesOnRoads, how = "inner", on = "count_point_id")

    # Group the pedal_cycles column 
    hospitalsCycles = hospitalsCycles.groupby(["city","latitude","longitude","name",
                                           "count_point_id","distance"], 
                                          as_index=False)["pedal_cycles"].sum()

    return hospitalsCycles

def MarketBikes():

    # Load data and select top 5 cities
    rawData = LoadData()
    cityRoads = CityData(rawData)

    # Load Market data
    marketInfo = Markets()

    marketCoordinates = marketInfo[["latitude", "longitude"]]

    closest_roadpoint = []
    distance_roadpoint = []

    #t1 = time.perf_counter()
    
    # Find the geodesic distance to a key place
    for i in range(0, len(marketInfo)):
        coordinates = (marketCoordinates.iloc[i,0], marketCoordinates.iloc[i,1])
        cityRoads[f"market_{i}"] = cityRoads.apply(lambda row: GetDistance(coordinates, row), axis=1)

        minDistance = cityRoads[f"market_{i}"].min()
        idx = cityRoads[f"market_{i}"].idxmin()

        roadpoint = cityRoads.iloc[idx,0]

        closest_roadpoint.append(roadpoint)
        distance_roadpoint.append(minDistance)

    #t2 = time.perf_counter()
    #print(t2 - t1) #timer

    marketInfo["count_point_id"] = closest_roadpoint
    marketInfo["distance"] = distance_roadpoint

    bikesOnRoads = cityRoads[["count_point_id","pedal_cycles"]]

    marketsCycles = pd.merge(marketInfo, bikesOnRoads, how = "inner", on = "count_point_id")

    # Sum the pedal_cycles column 
    marketsCycles = marketsCycles.groupby(["city","latitude","longitude","name",
                                           "count_point_id","distance"], 
                                          as_index=False)["pedal_cycles"].sum()

    return marketsCycles

# this is the whole dataframe
# hospital = HospitalBikes()
# market = MarketBikes()

# select only pedal_cycles and then get a list
# hospital_list = hospital["pedal_cycles"].tolist()
# market_list = market["pedal_cycles"].tolist()