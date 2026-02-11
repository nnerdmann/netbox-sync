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


def _resolve_log_level(args):
    if args.debug:
        return logging.DEBUG

    if args.verbose >= 2:
        return logging.DEBUG
    if args.verbose == 1:
        return logging.INFO

    return getattr(logging, args.log_level.upper(), logging.WARNING)


def configure_logging(args):
    log_level = _resolve_log_level(args)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.debug("Logging configured with level %s", logging.getLevelName(log_level))

    if not args.smtp_to:
        logger.debug("SMTP logging disabled because no --smtp-to recipients were provided")
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
    logger.debug(
        "Configured SMTP error logging to %s via %s:%s",
        ", ".join(args.smtp_to),
        args.smtp_host,
        args.smtp_port,
    )


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
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Set application log level (default: WARNING)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v=INFO, -vv=DEBUG)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (equivalent to --log-level DEBUG)",
    )
    
    args = parser.parse_args()
    
    configure_logging(args)
    logger.info("Starting NetBox sync")
    logger.debug("Runtime arguments: %s", {k: v for k, v in vars(args).items() if "token" not in k and "password" not in k})
    
    con_master = api(args.master_url, token=args.master_token)
    con_slave = api(args.slave_url, token=args.slave_token)
    logger.debug("Initialized master and slave NetBox API clients")

    # racks = Racks(con_master, con_slave, args.mapping)
    # racks.sync()
    logger.debug("Starting device synchronization")
    devices = Devices(con_master, con_slave, args.mapping)
    devices.sync()
    # modbay = ModuleBays(con_master, con_slave, args.mapping)
    # modbay.sync()
    logger.debug("Starting device bay synchronization")
    devbay = DeviceBays(con_master, con_slave, args.mapping)
    devbay.sync()
    logger.debug("Starting interface synchronization")
    interfaces = Interfaces(con_master, con_slave, args.mapping)
    interfaces.sync()
    logger.debug("Starting cluster type synchronization")
    cluster_types = ClusterTypes(con_master, con_slave, args.mapping)
    cluster_types.sync()
    logger.debug("Starting cluster group synchronization")
    cluster_groups = ClusterGroups(con_master, con_slave, args.mapping)
    cluster_groups.sync()
    logger.debug("Starting cluster synchronization")
    clusters = Clusters(con_master, con_slave, args.mapping)
    clusters.sync()
    logger.debug("Starting virtual machine synchronization")
    virtual_machines = VirtualMachines(con_master, con_slave, args.mapping)
    virtual_machines.sync()
    logger.debug("Starting virtual interface synchronization")
    virtual_interfaces = VirtualInterfaces(con_master, con_slave, args.mapping)
    virtual_interfaces.sync()
              
    
    
    logger.info("Sync completed")


if __name__ == "__main__":
    main()
