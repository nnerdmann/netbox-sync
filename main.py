import argparse
import logging
from pynetbox import api

from sync.racks import Racks
from sync.devices import Devices
from sync.modules_bays import ModuleBays
from sync.device_bays import DeviceBays
from sync.interfaces import Interfaces


# main.py

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Sync NetBox instances")
    parser.add_argument("--master-url", required=True, help="Master NetBox URL")
    parser.add_argument("--master-token", required=True, help="Master NetBox API token")
    parser.add_argument("--slave-url", required=True, help="Slave NetBox URL")
    parser.add_argument("--slave-token", required=True, help="Slave NetBox API token")
    parser.add_argument("--mapping", type=str, help="JSON file for mapping")
    
    args = parser.parse_args()
    
    logger.info("Starting NetBox sync")
    
    con_master = api(args.master_url, token=args.master_token)
    con_slave = api(args.slave_url, token=args.slave_token)
    
    # racks = Racks(con_master, con_slave, args.mapping)
    # racks.sync()
    devices = Devices(con_master, con_slave, args.mapping)
    devices.sync()
    # modbay = ModuleBays(con_master, con_slave, args.mapping)
    # modbay.sync()
    devbay = DeviceBays(con_master, con_slave, args.mapping)
    devbay.sync()
    interfaces = Interfaces(con_master, con_slave, args.mapping)
    interfaces.sync()
              
    
    
    logger.info("Sync completed")


if __name__ == "__main__":
    main()