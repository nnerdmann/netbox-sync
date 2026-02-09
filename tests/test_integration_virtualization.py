import os
import uuid

import pytest

pynetbox = pytest.importorskip("pynetbox")
from pynetbox import api

from sync.cluster_groups import ClusterGroups
from sync.cluster_types import ClusterTypes
from sync.clusters import Clusters
from sync.sync import Sync
from sync.virtual_interfaces import VirtualInterfaces
from sync.virtual_machines import VirtualMachines


ENV_VARS = (
    "NETBOX_MASTER_URL",
    "NETBOX_MASTER_TOKEN",
    "NETBOX_SLAVE_URL",
    "NETBOX_SLAVE_TOKEN",
)


def _require_env():
    missing = [name for name in ENV_VARS if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing NetBox env vars: {', '.join(missing)}")


def _get_connections():
    _require_env()
    master = api(os.environ["NETBOX_MASTER_URL"], token=os.environ["NETBOX_MASTER_TOKEN"])
    slave = api(os.environ["NETBOX_SLAVE_URL"], token=os.environ["NETBOX_SLAVE_TOKEN"])
    return master, slave


def _ensure_tenant(connection, slug):
    tenant = connection.tenancy.tenants.get(slug=slug)
    if tenant is None:
        tenant = connection.tenancy.tenants.create({"name": slug, "slug": slug})
    return tenant


def _delete_if_exists(endpoint, **filters):
    obj = endpoint.get(**filters)
    if obj is not None:
        obj.delete()


def _delete_vm_interfaces(connection, vm_name):
    vm = connection.virtualization.virtual_machines.get(name=vm_name)
    if vm is None:
        return
    for iface in connection.virtualization.interfaces.filter(virtual_machine_id=vm.id):
        iface.delete()


def test_virtualization_sync_against_live_netbox():
    master, slave = _get_connections()
    unique = f"netbox-sync-{uuid.uuid4().hex[:8]}"

    tenant_slug = Sync.global_sync_values["tenant"]["slug"]
    _ensure_tenant(master, tenant_slug)
    _ensure_tenant(slave, tenant_slug)

    created_master = []
    created_slave = []

    try:
        cluster_type = master.virtualization.cluster_types.create(
            {"name": f"{unique}-type", "slug": f"{unique}-type"}
        )
        created_master.append(cluster_type)

        cluster_group = master.virtualization.cluster_groups.create(
            {"name": f"{unique}-group", "slug": f"{unique}-group"}
        )
        created_master.append(cluster_group)

        cluster = master.virtualization.clusters.create(
            {
                "name": f"{unique}-cluster",
                "type": cluster_type.id,
                "group": cluster_group.id,
                "tenant": {"slug": tenant_slug},
            }
        )
        created_master.append(cluster)

        virtual_machine = master.virtualization.virtual_machines.create(
            {
                "name": f"{unique}-vm",
                "cluster": cluster.id,
                "status": "active",
                "tenant": {"slug": tenant_slug},
            }
        )
        created_master.append(virtual_machine)

        interface = master.virtualization.interfaces.create(
            {
                "name": "eth0",
                "virtual_machine": virtual_machine.id,
                "enabled": True,
            }
        )
        created_master.append(interface)

        ClusterTypes(master, slave).sync()
        ClusterGroups(master, slave).sync()
        Clusters(master, slave).sync()
        VirtualMachines(master, slave).sync()
        VirtualInterfaces(master, slave).sync()

        slave_type = slave.virtualization.cluster_types.get(name=f"{unique}-type")
        assert slave_type is not None
        created_slave.append(slave_type)

        slave_group = slave.virtualization.cluster_groups.get(name=f"{unique}-group")
        assert slave_group is not None
        created_slave.append(slave_group)

        slave_cluster = slave.virtualization.clusters.get(name=f"{unique}-cluster")
        assert slave_cluster is not None
        created_slave.append(slave_cluster)

        slave_vm = slave.virtualization.virtual_machines.get(name=f"{unique}-vm")
        assert slave_vm is not None
        created_slave.append(slave_vm)

        slave_iface = slave.virtualization.interfaces.get(
            name="eth0", virtual_machine_id=slave_vm.id
        )
        assert slave_iface is not None
        created_slave.append(slave_iface)
    finally:
        for obj in reversed(created_slave):
            obj.delete()
        for obj in reversed(created_master):
            obj.delete()
        _delete_vm_interfaces(master, f"{unique}-vm")
        _delete_vm_interfaces(slave, f"{unique}-vm")
        _delete_if_exists(master.virtualization.cluster_types, name=f"{unique}-type")
        _delete_if_exists(master.virtualization.cluster_groups, name=f"{unique}-group")
        _delete_if_exists(master.virtualization.clusters, name=f"{unique}-cluster")
        _delete_if_exists(master.virtualization.virtual_machines, name=f"{unique}-vm")
        _delete_if_exists(slave.virtualization.cluster_types, name=f"{unique}-type")
        _delete_if_exists(slave.virtualization.cluster_groups, name=f"{unique}-group")
        _delete_if_exists(slave.virtualization.clusters, name=f"{unique}-cluster")
        _delete_if_exists(slave.virtualization.virtual_machines, name=f"{unique}-vm")
