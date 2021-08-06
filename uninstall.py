import os
import re
import shutil

print("Uninstalling trip_overview app...")
path_to_app = "/etc/capsule/trip_overview"
path_to_var = "/var/opt/trip_overview"
path_to_log = "/var/log/capsule/trip_overview"
path_to_conf = "/etc/capsule/trip_overview/config.yaml"
path_to_services = "/etc/systemd/system/trip_overview.service"
if os.path.exists(path_to_app):
    print("Remove folder", path_to_app)
    shutil.rmtree(path_to_app)
if os.path.exists(path_to_var):
    print("Remove folder", path_to_var)
    shutil.rmtree(path_to_var)
if os.path.exists(path_to_log):
    print("Remove folder", path_to_log)
    shutil.rmtree(path_to_log)
if os.path.exists(path_to_services):
    print("Remove trip_overview service")
    os.system("systemctl stop trip_overview.service")
    os.system("systemctl disable trip_overview.service")
    os.system("systemctl daemon-reload")
    os.remove(path_to_services)