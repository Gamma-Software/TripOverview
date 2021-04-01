*Date of creation: 31/03/2021*

# TripOverview
Keeps track of the place where the vehicle moves and sleeps and gives an overview of the road trip.

## Features
- Store the gps position at a certain interval
- 

## Requirements
TODO

## Details
### Programming Language
This project is written in python and is meant to be run on a device that supports GPS queries.

### Integration
TODO

### Features
- Store the gps position at a certain interval: 
  - In a CSV file with the values => timestamp / lat / lon
  - Depending on the database size => split the data monthly
- Display the current trip:
  - Current trip location
  - Mark the places where the vehicle stayed at night
  - Display the date_time/lat/lon/km_travelled
  - Trace the position
  - Dynamically see the progression
