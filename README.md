# GEOGloWS ECMWF Streamflow Hydroviewer - Tethys Web App

Developed by Riley Hales and Kyler Ashby, 2020
(c) Riley Hales, Kyler Ashby, BYU Hydroinformatics Lab

Provides an interactive map interface for:

1. Viewing animated streamflow forecast maps provided by an ESRI Dynamic Mapping Service from the Living Atlas
1. Retrieving streamflow data for particular river segments via the Streamflow REST API hosted by ECMWF
1. Performing post-processing streamflow calibration using measured discharge including integration with selected national discharge gauge networks 

Provides a utility for creating hydroviewers for subsets of the global model

1. Clip global model shapefiles to extents of:
    - Boundaries drawn on a map
    - A shapefile or geojson of boundaries
    - Predefined country or world region borders (ESRI Living Atlas)
1. Export clipped shapefiles:
    - To a specified geoserver
    - As a zip archive
    - (beta) As a Hydroshare resource (requires log in to tethys via hydroshare)
1. Export the fully functioning hydroviewer as an HTML file.

How to get the global delineation shapefiles required for the Hydroviewer Creator functions:

1. Download them all from Hydroshare https://www.hydroshare.org/resource/d5155cb57987489a95b83364d2c0f6c0/ 
1. Transfer the shapefiles to the web server hosting this app
1. Place them in the app workspace folder for the app (the default custom setting value) or in any other folder and change the custom setting to match the folder where you placed the contents
1. Be sure that you organize the shapefiles in a folder that contains the 1 folder for each of the 13 global regions. Each of the folders for the global regions should contain 3 folders for the boundary, catchment, and drainagline shapefiles. Each of those 3 folders should contain 1 shapefile).
