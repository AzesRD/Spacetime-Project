# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 16:51:35 2021

GEOM4009- Report 3: Draft Code

Authors: Rajpal, Jacob, Joshua, Yussuf, Gillian

The following code aims to:
-Read in a dataframe containing at least an Object_ID, X positional data, Y positional data, and Timestamp data
        - identify which column represent object ID
        - which columns represent x,y positional data
        - which column represents time data
-Simplify the number of points within the data using Ramer–Douglas–Peucker algorithm
-Determine the time span in the dataset
-Decide on the vertical exaggeration (time scale) of the data
-Convert 2D point data into a 3D dataset with time represented on Z axis – join points with lines
-Export to KML (or other format) for display 
-determine the distance between two objects at all shared time-measurements

"""


import os
import pandas as pd
import geopandas as gpd
import datetime
import numpy as np
from shapely.geometry import Point
from shapely.geometry import LineString
import fiona
from time import time
from sklearn.neighbors import DistanceMetric


#Gillian's function
def set_directory (directory_path): #This function auto-sets the directory based on user specified pathway
        """
        Parameters
        ----------
        Directory_path : Pathway to the user directory
            Used to set the directory and determine where to search for files 
    
        Returns
        ------- 
        A directory set by the user   #*# Actually this doesn't return anything... (None)
    
        """
        direct= directory_path 
        try:
            os.chdir(direct) #to set the directory specified by the user
            os.listdir() #This will allow the user to check that the directory is in the location
        except:
            print("There is something wrong with the directory inputted") #Warns the user they did not type in directory name properly
 

#Gillian's function
def read_file (filename, ob_id, x, y,time_pos):  
        """
        Parameters
        ----------
        filename : name of csv file
            filename is used to locate file in the directory to be read in as dataframe
            
        Returns
        -------
        a pandas dataframe
    
        """
        try:
            df = pd.read_csv(filename)# Here the main files will be read in as a pandas dataframe by the user 
            id_num= int(ob_id- 1) #subtracting 1 as the index starts at 0 in python
            x_col= int(x-1) #subtracting 1 as the index starts at 0 in python
            y_col= int(y-1) #subtracting 1 as the index starts at 0 in python
            time= int(time_pos-1) #subtracting 1 as the index starts at 0 in python
            new_df=df.rename(columns={df.columns[id_num]: "object_id", #renaming the columns by user specified index values
                                df.columns[x_col]: "x_pos_data",
                                df.columns[y_col]: "y_pos_data",
                                df.columns[time]: "timestamp"})
        
        except:
            print ("filename could not be found")
        
        return new_df

#Jacob's function            
def firstLast (df):   #*# time column already renamed so you don't need position
    """
    #*# What does this function do? 

    Parameters
    ----------
    df : TYPE
        Calling on the converted geospatial dataframe from the previous function.
        This geospatial dataframe has the renamed columns that will be used throughout the code
    time_pos : TYPE
        This is what will be called on later in the command line
        when  the user puts the column number containing timestamp values.

    Returns
    -------
    None.

    """
## Here, the the variables start time and end time are assigned by 
## picking the first, and last row of the time position column
 
    #df['timestamp'] = pd.to_datetime(df['timestamp'], infer_datetime_format=True)
    df['timestamp']=pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M')
    time_df= df.sort_values(by="timestamp")
    time= time_df["timestamp"] 
    startTime = time.iloc[0]
    endTime = time.iloc[-1]   
    difference = endTime - startTime
    return startTime, endTime, difference 

          
#Yussuf's function
def simple(df, lats , longs):
    """
    Parameters
    ----------
    df : dataframe
    lats : Latitude ID
    longs : Longitude ID

    Returns
    -------
    result : Simplified df 

    """
    #creates a empty df to concat all the simplfied versions too 
    result = pd.DataFrame()
    
    #grabs all the unique ID's from the original df
    names = df['object_id'].unique()
    grouped = df.groupby(df.object_id)
    

    print("Will be simplifying with a tolerence of 0.015 degrees. This can be changed in the script by changing the tolerence variable")
    for i in range(len(names)):
       #assigns name_id to the first name in the names variable 
       name_id = grouped.get_group(names[i])
       #Gets all the coordinates from specific nameID
       coordinates = name_id[[lats, longs]].to_numpy()
       line = LineString(coordinates)
       print(" ")
    
       
       # all points in the simplified object will be within the tolerance distance of the original geometry can be changed to whatever the User wants
       tolerance = 0.015
        
       # if preserve topology is set to False the much quicker Douglas-Peucker algorithm is used
       # we don't need to preserve topology bc we just need a set of points, not the relationship between them
       simplified_line = line.simplify(tolerance, preserve_topology=False)
       #The code Undernearth works depending on the file not sure why but it is useful to have if the file is compatible
       #print("\nCurrenlty compressing subset", names[i] + ".", "Which is subset",   i +1 , "out of " , len(names))
       print(len(line.coords), 'coordinate pairs in full data set')
       print(len(simplified_line.coords), 'coordinate pairs in simplified data set')
       print(round(((1 - float(len(simplified_line.coords)) / float(len(line.coords))) * 100), 1), 'percent compressed')
        
        
       # save the simplified set of coordinates as a new dataframe
       lon = pd.Series(pd.Series(simplified_line.coords.xy)[1])
       lat = pd.Series(pd.Series(simplified_line.coords.xy)[0])
       si = pd.DataFrame({longs:lon, lats:lat})
       si.tail()
        
       start_time = time()
        
       # df_label column will contain the label of the matching row from the original full data set
       si['df_label'] = None
        
       # for each coordinate pair in the simplified set
       for si_label, si_row in si.iterrows():    
            si_coords = (si_row[lats], si_row[longs])
            
            # for each coordinate pair in the original full data set
            for df_label, df_row in df.iterrows():
                
                # compare tuples of coordinates, if the points match, save this row's label as the matching one
                if si_coords == (df_row[lats], df_row[longs]):
                    si.loc[si_label, 'df_label'] = df_label
                    break
                    
       print('process took %s seconds' % round(time() - start_time, 2))
        
       # select the rows from the original full data set whose labels appear in the df_label column of the simplified data set
       rs = df.loc[si['df_label'].dropna().values]
       result = pd.concat([rs, result])
   
       rs.tail()
    #Returns updated simplify version   

    #Some of the code was taken from here: https://geoffboeing.com/2014/08/reducing-spatial-data-set-size-with-douglas-peucker/ 
    return result

#Rajpal's function   
def haversine(Olat,Olon, Dlat,Dlon):
    #Source: https://www.betterdatascience.com/heres-how-to-calculate-distance-between-2-geolocations-in-python/
    """
    Parameters
    ----------
    Olat : minimum latitude 
    Olon : minimum longitude 
    Dlat : maximum latitude
    Dlon : maximum longitude
   
    Returns
    -------
    distance in radians
    
    
    haversine function finds the distance between the minimum lat and long points to the maximum lat and 
    long points

    """
    
    radius = 6371.  #radius of the Earth in km

    d_lat = np.radians(Dlat - Olat) #finds the difference between max Latitude and min Latitude, and then converts to radians
    d_lon = np.radians(Dlon - Olon) #finds the difference between max Longitude and min Longitude, and then converts to radians
    a = (np.sin(d_lat / 2.) * np.sin(d_lat / 2.) +
         np.cos(np.radians(Olat)) * np.cos(np.radians(Dlat)) *
         np.sin(d_lon / 2.) * np.sin(d_lon / 2.))
    c = 2. * np.arctan2(np.sqrt(a), np.sqrt(1. - a))
    d = radius * c

    return d

#Rajpal's function  
def zScale(df):
    
    """
    x= np.linspace(0,50)
    y, z= np.linspace(0, 50, 50, False, True)
    T= np.linspace(0, 200, 50, False)
    b= np.arange(0, 200, 200/50) #same as T 200/50 - gives the increment to create same array as T - 1 to 200, with 50 elements
    
    
    print(b)
    b.size
    
    df = pd.DataFrame(x, columns = ['X'])
    """    
    
    ID=df.object_id
    x=df.x_pos_data
    y=df.y_pos_data
    z=df.timestamp
    
    time=pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M')
    time= time.dt.strftime('%Y%m%d').astype(float)
    
    df['time'] = pd.Series(time)
    
    zmin = 500
    zmax = 10200
    
    z3 = np.linspace(zmin, zmax, df.time.size)
    
    t1 = time.min()
    t2 = time.max()
    
    t1=zmin
    t2=zmax
    
    s = (zmax-zmin)/(t2 -t1)

    
    #y1 = slope*x1 + c
    
    c = y.min()- s*(x.min())
    
    z4 = 1*time + c
    
    """
    A = np.empty(df['BeginTime'].size) #gives entire column size of df; A is a numpy array 
    
    
    
    #df = pd.DataFrame(A, columns = ['A']) used to create a pd df and then initalize it with a column
    
    a,b = np.unique(ID, return_counts=True)
    a = ID.unique()
    
    
    
    c=0
    k=0
    for i in ID.unique():
        j=0;
        while(j<b[c]):
            A[k] = j
            #np.append(A,j)
            j=j+1
            k=k+1
        c=c+1
    
    df['A'] = pd.Series(A) #adds A to df
        
    T=A*10000000
    
    z1 = np.linspace(0,1,1232) * 10
    df['z1'] = pd.Series(z1) #adds A to df
    
    z2 = np.linspace(78, 81, 1232)
    df['z2'] = pd.Series(z2) #adds A to df

    
    """
    
    return z3

#Joshua's function
def PointsLine(df, z1):
    """
    #*# What does this function do? 

    Parameters
    ----------
    obj_id_pos: Data Identifier 
        Identifier necessary for the geoseries 
    x_pos : X value(positional)
        The x position of the tiger 
    y_pos : Y value(positional)
        The y position of the tiger
    time_pos : Z value(time)
        The time assigned to each tiger position

    Returns
    -------
    A KML File with the finished visualization 

    """
    
    #Making sure it's in WGS 84
    proj='EPSG:4326'
    #Creating a line while zipping 3 coordinates(3 dimension)
    objects=df.object_id.unique() #finding all the unique object ids
    index_list=[]
    geometry_list=[]
    for ob in objects: #looping through ids
        ob_df= df.loc[df["object_id"]== ob] #subsetting pandas dataframe to the specific object
        ob_line=LineString(zip(ob_df.x_pos_data, ob_df.y_pos_data, z1)) 
        index_list.append(ob)
        geometry_list.append(ob_line)
       
    line_gd=gpd.GeoDataFrame(index=index_list,crs=proj,geometry=geometry_list)

    return line_gd
   
#Joshua's function   
def KMLExport(line_gd):  #*# you should be able to export the points too... right? 
    #*# docstring.... 
    #It was not so I added it 
    fiona.supported_drivers['KML']='rw'
    fiona.supported_drivers['LIBKML'] = 'rw' # enable KML support which is disabled by default
    KMLexport=line_gd.to_file('finalproject.kml',driver="KML") 
    
    #Then open the created KML to export in altitude mode
    
    return KMLexport

#Gillian's function
def distance_bw_2objs(df, object_id_1, object_id_2):
    """
    Parameters
    ----------
    df : dataframe
        dataframe containing the objects of interest
    object_id_1 : object id value 1
        the first object of interest (within the inputted dataframe)
    object_id_2 : object id value 2
        the second object of interest (within the inputted dataframe)
    Returns
    -------
    object_distances : distance in kilometers
        finds all the shared timestamp values between the two objects, 
        and calculates the distance between the two objects at each matching time value

    """
    try:
        df_filter= df[(df["object_id"] == object_id_1) | (df["object_id"] == object_id_2)] #filtering the dataframe for two objects of interest
        
        duplicate_dates= df_filter.groupby("timestamp").filter(lambda x: len(x) == 2) #Only dates that show up for both objects
       
        ob_1_df= duplicate_dates[duplicate_dates["object_id"]==object_id_1] #turns just object one into a dataframe
        ob1x_arr = np.asarray(ob_1_df['x_pos_data']) #turns object one's x position values into an array (easy for looping through to calculate distance)
        ob1y_arr =np.asarray(ob_1_df['y_pos_data']) #turns object one's y position values into an array (easy for looping through to calculate distance)
        
        ob_2_df= duplicate_dates[duplicate_dates["object_id"]== object_id_2] #turns just object 2 into a dataframe
        ob2x_arr = np.asarray(ob_2_df['x_pos_data']) #turns object two's x position values into an array (easy for looping through to calculate distance)
        ob2y_arr =np.asarray(ob_2_df['y_pos_data']) #turns object two's y position values into an array (easy for looping through to calculate distance)
        
        distances= [] #an array to store the calculated distance at each time interval
        
        for i in range(len(ob1x_arr)): 
            hs_dist= haversine(ob1x_arr[i], ob1y_arr[i], ob2x_arr[i], ob2y_arr[i])
            distances.append(hs_dist)
            
        object_distances = ob_1_df[['timestamp']].copy() #create a new dataframe with the timestamp values from the object dataframes
        object_distances.insert(1, "distance_km", distances) #append the calculated distances to 
       
        mean= sum(distances)/len(distances)
        st_dev= np.std(distances) 
        cov= st_dev / mean
    except:
        print("There are no shared time values between these two objects")
       
    return object_distances, mean, st_dev, cov

#Gillian's function
def distance_matrix (df, time_interval):
## Code sourced from: https://kanoki.org/2019/12/27/how-to-calculate-distance-in-python-and-pandas-using-scipy-spatial-and-distance-functions/
    """
    Parameters
    ----------
    df : dataframe
        DESCRIPTION.
    time_interval : timestamp
        the specific time measurement of interest (e.g. 2019/07/09 10:32)

    Returns
    -------
    distance_matrix : dataframe
        Finds all objects that contain measurements at a specific date, and then calculates the distances
        between all objects at that point  in time

    """
    try:
        dist = DistanceMetric.get_metric('haversine')
        df_filter= df.loc[df["timestamp"]== time_interval]
        df_filter.loc[:,"x_pos_data"]=np.radians(df_filter['x_pos_data'])
        df_filter.loc[:,"y_pos_data"]=np.radians(df_filter['y_pos_data'])
        
        distance_matrix= pd.DataFrame(dist.pairwise(df_filter[['x_pos_data','y_pos_data']].to_numpy())*6373,  
                                      columns=df.object_id.unique(), index= df.object_id.unique())
    except:
        print("Try a different timestamp value")
        
    return distance_matrix




def main():
    direct= str(input("Please input directory path: ")) #prompts user to give path of directory
    set_directory(direct) #sets directory path

    file= str(input("Please input name of file to be read (with .csv extension): ")) #prompts user to specify file of interest within their set directory
    
    obj_id_pos= int(input("Please input the column number containing object ID values: ")) #user specifies where there unique ID is in original file
    x_pos= int(input("Please input the column number containing x values: ")) #user specifies where their x data is in original file
    y_pos= int (input("Please input the column number containing y values: ")) #user specifies where their y data is in original file
    time_pos= int(input("Please input the column number containing timestamp values: ")) #user specifies where their timestamp data is in original file
    
    #step 1 rename the dataframe
    df= read_file(file, obj_id_pos, x_pos, y_pos, time_pos) #reads in the user file as a dataframe #this reassigns all columns for consistent naming throughout the code


    #step 2: Simplifying the number of points in the dataframe
    simpleVersion = simple(df, 'x_pos_data', 'y_pos_data')
    print(simpleVersion)

    #step 3 - determine the timespan of the dataset. The start time and endtime
    start, end, timespan= firstLast(simpleVersion) 
 
    #step 5: vertical exaggeration
    z = zScale(simpleVersion)
    
    #step 6: convert 2D to 3D
    line_gd = PointsLine(simpleVersion, z)
    
    
    #step 7: distance between objects calculated (user inputs object IDs)
    object1=input("Please give the object ID for the first object of interest")
    object2=input("Please give the object ID for the second object of interest")
    dist, mean_dist, std_dist, cov_dist= distance_bw_2objs(simpleVersion, object1, object2)
    print(dist)
    
    # distance matrix for a specific date
    dist_matrix= distance_matrix(simpleVersion, "2019-01-01 00:00:00")
    print(dist_matrix)
    
    #step 8 export to KML
    KMLExport(line_gd)
    
    #Open the KML and re-write in altitude mode
    kml = open("finalproject.kml", "r")
    old = "<LineString><coordinates>"
    new = "<LineString><altitudeMode>absolute</altitudeMode><coordinates>"
    kml_str = kml.read()
    kml_str =  kml_str.replace(old, new)
    kml.close()
    kml = open("finalproject.kml", "w")
    kml.write(kml_str)
    kml.close()
    
if __name__=="__main__":
    main()



