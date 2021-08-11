import os
import re
import shutil

print("Configuring trip_overview app...")
path_to_app = "/etc/capsule/trip_overview"
path_to_var = "/var/opt/trip_overview/saves"
path_to_log = "/var/log/capsule"
path_to_conf = "/etc/capsule/trip_overview/config.yaml"
path_to_services = "/etc/systemd/system/trip_overview.service"
if not os.path.exists(path_to_app):
    print("Create folder", path_to_app)
    os.makedirs(path_to_app, 0o775)
    os.chown(path_to_app, 1000, 0) # Rudloff id and group Root
    os.chmod(path_to_app, 0o775) # Give all read access but Rudloff write access
if not os.path.exists(path_to_var):
    print("Create folder", path_to_var)
    os.makedirs(path_to_var, 0o775)
    os.chown(path_to_var, 1000, 0) # Rudloff id and group Root
    os.chmod(path_to_var, 0o775) # Give all read access but Rudloff write access
if not os.path.exists(path_to_log):
    print("Create folder", path_to_log)
    os.makedirs(path_to_log, 0o644)
    os.chown(path_to_log, 1000, 0) # Rudloff id and group Root
    os.chmod(path_to_log, 0o775) # Give all read access but Rudloff write access
if not os.path.exists(path_to_conf):
    print("Create trip_overview configuration")
    shutil.copy2(os.path.join(os.path.dirname(__file__), "default_config.yaml"), path_to_conf)
    os.chown(path_to_conf, 1000, 0) # Rudloff id and group Root
    os.chmod(path_to_conf, 0o775) # Give all read access but Rudloff write access
if not os.path.exists(path_to_services):
    print("Create trip_overview service")
    shutil.copy2(os.path.join(os.path.dirname(__file__), "trip_overview.service"), path_to_services)
    os.chmod(path_to_services, 0o775) # Give all read access but Rudloff write access
    os.system("systemctl daemon-reload")
    os.system("systemctl enable trip_overview.service")