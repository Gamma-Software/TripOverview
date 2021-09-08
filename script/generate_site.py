#!/usr/bin/python3
# This script will retrieve the raw data from the influx data from the last update,
# store the data in a custom sql database and generate the site

import io
import os
import yaml
import sys
import time
import logging
import datetime
from methods import *
from influxdb import DataFrameClient
from OverviewDatabase import OverviewDatabase


# ----------------------------------------------------------------------------------------------------------------------
# Read script parameters
# ----------------------------------------------------------------------------------------------------------------------
path_to_conf = os.path.join("/etc/capsule/trip_overview/config.yaml")
# If the default configuration is not install, then configure w/ the default one
if not os.path.exists(path_to_conf):
    sys.exit("Configuration file %s does not exists. Please reinstall the app" % path_to_conf)
# load configuration
with open(path_to_conf, "r") as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)

# ----------------------------------------------------------------------------------------------------------------------
# Initiate variables
# ----------------------------------------------------------------------------------------------------------------------
connected = False
logging.basicConfig(
    filename="/var/log/capsule/trip_overview.log",
    filemode="a",
    level=logging.DEBUG if conf["debug"] else logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')

# Influxbd client
influxdb_client =  DataFrameClient(conf["influxdb"]["url"], conf["influxdb"]["port"], conf["influxdb"]["user"], conf["influxdb"]["pass"], conf["influxdb"]["database"])

# Overview database
logging.info("connect to database located in " + conf["database_filepath"])
trip_data = OverviewDatabase()
trip_data.connect_to_database(conf["database_filepath"], True)


# ----------------------------------------------------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------------------------------------------------
try:
    # Check when the site was updated, if first time then use yesterday’s date
    now = datetime.now()
    last_update = datetime(now.year, now.month, now.day-1, now.hour, now.minute, now.second)
    if os.path.exists("/etc/capsule/trip_overview/last_site_update.txt"):
        with open("/etc/capsule/trip_overview/last_site_update.txt", "r") as f:
            isoformat_date = f.readline().strip("\n")
            last_update = datetime.fromisoformat(isoformat_date)
            logging.info("last update of the site was " + isoformat_date)
    
    # Check if the last time the trip overview is generated is older than 12h (or 60*60*12=43200s) at least
    if (now - last_update).seconds > 43200:
        # Get the datas from influxdb with some grouping policies
        df = retrieve_influxdb_data(
            [last_update.isoformat(), now.isoformat()],
            influxdb_client, "5s")
        
        # Save the digests data in a different database
        trip_data.commit_dataframe(df)

        logging.info("Generate Trip overview at "+conf["folium_site_output_path"])
        create_site(trip_data, conf["folium_site_output_path"], now.strftime("%Y_%m_%d"), conf["map_generation"]["url"])

        # Store last update of site
        with open("/etc/capsule/trip_overview/last_site_update.txt", "w+") as f:
            f.write(str(now.isoformat()))
    else:
        print("Trip overview already updated")
        logging.info("Trip overview already updated")
except KeyboardInterrupt:
    logging.info("Trip overview generation aborted by user")
    pass

logging.info("Stop script")
sys.exit(0)
