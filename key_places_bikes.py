import pandas as pd
import numpy as np
import seaborn
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import time
import os
import scipy as sc

def Hospitals():

    '''
    This function loads the Hospitals.csv file  as a pandas dataframe.
    It will convert the latitude and longitude coordinates to float types to
    keep the distance calculations consistent

    Input: None
    Output: hospitalData (Hospital dataframe) 
    '''

    # Get the current directory and import the csv 
    curDir = os.getcwd()
    hospitalCsv = os.path.join(curDir,"Hospital.csv")

    # Get the dataframe and convert the coordinates columns into floats
    hospitalData = pd.read_csv(hospitalCsv, dtype={"latitude": float, "longitude": float}, 
                            usecols=["city","latitude","longitude", "name"])
    
    return hospitalData

def Markets():

    '''
    This function loads the Main_markets.csv file  as a pandas dataframe.
    It will convert the latitude and longitude coordinates to float types to
    keep the distance calculations consistent

    Input: None

    Output: 
    marketData (Market dataframe) 
    '''

    #Get the current directory and import the csv 
    curDir = os.getcwd()
    marketCsv = os.path.join(curDir,"Main_markets.csv")

    #Import the csv and convert the coordinates columns into float
    marketData = pd.read_csv(marketCsv, dtype={"latitude": float, "longitude": float}, 
                            usecols=["city","latitude","longitude", "name"])

    return marketData

def GetDistance(keyPlace, roadpoint):
    '''
    This mini-script will be used for calculating the geodesic distance between
    two places, a key place and the road point, using the geodesic function of 
    geopy. This is an approximation of a distance.

    Inputs:
    keyPlace: Specific spot (market or hospital) to calculate the distance from.
              The expected type is a tuple containing the coordinates (lat, long)
    
    roadpoint: pandas dataframe containing the roadpoints. 

    Output:
    calculatedDistance = Geodesic distance (in km) rounded to 2 decimals

    '''
    
    # Create the tuple containing the roadpoint coordinates
    roadPoint = (roadpoint['latitude'], roadpoint['longitude'])

    #Calculate the distance in km and round to 2 decimales
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
     # as strings. Rename the "Year" column to reflect a more appropriate name

    rawData = pd.read_csv("dft_rawcount_region_id_3.csv", parse_dates = ["year"], 
                          dtype={'start_junction_road_name': str,
                                 'end_junction_road_name': str})
    rawData.rename(columns = {"year":"date"}, inplace = True)
    rawData["date"] = pd.to_datetime(rawData["date"], yearfirst = True, 
                      infer_datetime_format= True)

    # Create a new column called "year" and only store the year
    rawData["year"] = pd.to_datetime(rawData["date"], yearfirst = True).dt.year

    return rawData

def CityData(rawData):

    '''
    This function will call the DFT dataframe and will process only the top 5 cities
    in Scotland: Edinburgh, Glasgow, Perth, Aberdeen and Dundee

    Input
    rawData: DFT dataframe

    Output
    cityRoads: Filtered dataset containing the data for the top 5 cities
    
    '''

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
    
    '''
    This function will calculate the closest roadpoint to each hospital listed
    in the Hospital.csv file, and will output a dataframe containing the original
    Hospital csv file and the closest roadpoint, and the number of bicyles that 
    passed it.

    Input:  None

    Output
    hospitalCycles: Pandas dataframe containing the hospital information, closest
                    roadpoint and the number of cycles found in the whole dataset.
    '''

    # Load the top 5 cities data
    rawData = LoadData()
    cityRoads = CityData(rawData)

    # Load Hospitals data
    hospitalInfo = Hospitals()

    hospitalCoordinates = hospitalInfo[["latitude", "longitude"]]

    closest_roadpoint = []
    distance_roadpoint = []

    # Find the geodesic distance to a key place
    for i in range(0, len(hospitalInfo)):
        coordinates = (hospitalCoordinates.iloc[i,0], hospitalCoordinates.iloc[i,1])
        cityRoads[f"market_{i}"] = cityRoads.apply(lambda row: GetDistance(coordinates, row), axis=1)

        # Find the minimum distance and the index location
        minDistance = cityRoads[f"market_{i}"].min()
        idx = cityRoads[f"market_{i}"].idxmin()

        # Get the roadpoint id and append to a list
        roadpoint = cityRoads.iloc[idx,0]
        closest_roadpoint.append(roadpoint)
        distance_roadpoint.append(minDistance)

    # Add the filled lists into the dataframe as columns
    hospitalInfo["count_point_id"] = closest_roadpoint
    hospitalInfo["distance"] = distance_roadpoint

    # Select only the pedal_cycles columns and road point it from the DFT dataframe
    bikesOnRoads = cityRoads[["count_point_id","pedal_cycles"]]

    # Merge the datasets using inner join
    hospitalsCycles = pd.merge(hospitalInfo, bikesOnRoads, how = "inner", on = "count_point_id")

    # Group the pedal_cycles column and sum them
    hospitalsCycles = hospitalsCycles.groupby(["city","latitude","longitude","name",
                                           "count_point_id","distance"], 
                                          as_index=False)["pedal_cycles"].sum()

    return hospitalsCycles

def MarketBikes():

    '''
    This function will calculate the closest roadpoint to each markets listed
    in the Main_markets.csv file, and will output a dataframe containing the original
    Main_markets csv file and the closest roadpoint, and the number of bicyles that 
    passed it.

    Input:  None

    Output
    marketCycles: Pandas dataframe containing the market information, closest
                  roadpoint and the number of cycles found in the whole ddataset.
    '''

    # Load the top 5 cities data
    rawData = LoadData()
    cityRoads = CityData(rawData)

    # Load Market data
    marketInfo = Markets()

    marketCoordinates = marketInfo[["latitude", "longitude"]]

    closest_roadpoint = []
    distance_roadpoint = []

    
    # Find the geodesic distance to a key place
    for i in range(0, len(marketInfo)):
        coordinates = (marketCoordinates.iloc[i,0], marketCoordinates.iloc[i,1])
        cityRoads[f"market_{i}"] = cityRoads.apply(lambda row: GetDistance(coordinates, row), axis=1)
        
        # Find the minimum distance and the index location
        minDistance = cityRoads[f"market_{i}"].min()
        idx = cityRoads[f"market_{i}"].idxmin()

        # Get the roadpoint id and append to a list
        roadpoint = cityRoads.iloc[idx,0]
        closest_roadpoint.append(roadpoint)
        distance_roadpoint.append(minDistance)

    # Add the filled lists into the dataframe as columns
    marketInfo["count_point_id"] = closest_roadpoint
    marketInfo["distance"] = distance_roadpoint

    # Select only the pedal_cycles columns and road point it from the DFT dataframe
    bikesOnRoads = cityRoads[["count_point_id","pedal_cycles"]]

    # Merge the datasets using inner join
    marketsCycles = pd.merge(marketInfo, bikesOnRoads, how = "inner", on = "count_point_id")

    # Group the pedal_cycles column and sum them 
    marketsCycles = marketsCycles.groupby(["city","latitude","longitude","name",
                                           "count_point_id","distance"], 
                                          as_index=False)["pedal_cycles"].sum()

    return marketsCycles