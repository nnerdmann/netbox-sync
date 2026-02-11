import argparse
import logging
import logging.handlers
from pynetbox import api

from sync.racks import Racks
from sync.devices import Devices
from sync.modules_bays import ModuleBays
from sync.device_bays import DeviceBays
from sync.interfaces import Interfaces
from sync.cluster_types import ClusterTypes
from sync.cluster_groups import ClusterGroups
from sync.clusters import Clusters
from sync.virtual_machines import VirtualMachines
from sync.virtual_interfaces import VirtualInterfaces


# main.py

logger = logging.getLogger(__name__)


def configure_logging(args):
    logging.basicConfig(level=logging.INFO)
    if not args.smtp_to:
        return

    secure = () if args.smtp_starttls else None
    credentials = None
    if args.smtp_user and args.smtp_password:
        credentials = (args.smtp_user, args.smtp_password)

    handler = logging.handlers.SMTPHandler(
        mailhost=(args.smtp_host, args.smtp_port),
        fromaddr=args.smtp_from,
        toaddrs=args.smtp_to,
        subject=args.smtp_subject,
        credentials=credentials,
        secure=secure,
    )
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


def main():
    parser = argparse.ArgumentParser(description="Sync NetBox instances")
    parser.add_argument("--master-url", required=True, help="Master NetBox URL")
    parser.add_argument("--master-token", required=True, help="Master NetBox API token")
    parser.add_argument("--slave-url", required=True, help="Slave NetBox URL")
    parser.add_argument("--slave-token", required=True, help="Slave NetBox API token")
    parser.add_argument("--mapping", type=str, help="JSON file for mapping")
    parser.add_argument("--smtp-host", default="localhost", help="SMTP server host")
    parser.add_argument("--smtp-port", type=int, default=25, help="SMTP server port")
    parser.add_argument("--smtp-user", help="SMTP username")
    parser.add_argument("--smtp-password", help="SMTP password")
    parser.add_argument("--smtp-from", default="netbox-sync@example.com", help="SMTP from address")
    parser.add_argument("--smtp-to", action="append", help="SMTP recipient (repeatable)")
    parser.add_argument("--smtp-subject", default="NetBox sync errors", help="Email subject for error logs")
    parser.add_argument("--smtp-starttls", action="store_true", help="Enable STARTTLS for SMTP")
    
    args = parser.parse_args()
    
    configure_logging(args)
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
    cluster_types = ClusterTypes(con_master, con_slave, args.mapping)
    cluster_types.sync()
    cluster_groups = ClusterGroups(con_master, con_slave, args.mapping)
    cluster_groups.sync()
    clusters = Clusters(con_master, con_slave, args.mapping)
    clusters.sync()
    virtual_machines = VirtualMachines(con_master, con_slave, args.mapping)
    virtual_machines.sync()
    virtual_interfaces = VirtualInterfaces(con_master, con_slave, args.mapping)
    virtual_interfaces.sync()
              
    
    
    logger.info("Sync completed")


if __name__ == "__main__":
    main()
