from sync.sync import Sync

class Interfaces(Sync): 
   
    api_object = "dcim.interfaces"
    sync_parameters = ["name", "device", "type","description","parent","mgmt_only","enabled","mtu","mode","untagged_vlan"]
    unique_parameter = ["name","device"]
   
    def pre_sync(self, oldobj, newobj):
        # if newobj and "tagged_vlans" in newobj and newobj["tagged_vlans"] is not None:
        #     # Convert list of VLAN VIDs to list of VLAN object IDs
        #     # newobj["tagged_vlans"] contains the VID values - ensure they're integers
        #     vlans = [self.slave_conn.ipam.vlans.get(vid=vlan["vid"]) for vlan in newobj["tagged_vlans"]]
        #     newobj["tagged_vlans"] = [vlan.id for vlan in vlans]
        return newobj

    def sync_vlans(self, interface, vlans):
        """Sync Tagged VLANs for an interface."""
        new_vlans = []
        for vlan in vlans:
            vlan_obj = self.slave_conn.ipam.vlans.get(vid=vlan["vid"])
            if vlan_obj is not None:
                new_vlans.append(vlan_obj.id)
        interface.update({"tagged_vlans": new_vlans})          

    def post_sync(self, oldobj, newobj):      
        # Sync Tagged VLANs separately to avoid issues during creation/update
        if oldobj["tagged_vlans"] is not None and len(oldobj["tagged_vlans"]) > 0:
            self.sync_vlans(newobj, oldobj["tagged_vlans"])
        # Sync MAC Address separately to avoid issues during creation/update
        # if oldobj["mac_address"] is not None:
        #     self.sync_mac_address(newobj, oldobj["mac_addresses"])
        # Sync IP addresses separately to avoid issues during creation/update
        ips = self.master_conn.ipam.ip_addresses.filter(assigned_object_type="dcim.interface", assigned_object_id=oldobj["id"])
        if ips is not None and len(ips) > 0:
            self.sync_ip_addresses(newobj, ips)
        
        return newobj

    def sync_mac_address(self, interface, mac_addresses):
        """Sync MAC Address for an interface."""
        new_macs = []
        for mac in mac_addresses:
            mac_obj = self.slave_conn.dcim.mac_addresses.get(address=mac["mac_address"])
            if mac_obj is None:
                mac_obj = self.slave_conn.dcim.mac_addresses.create({
                    "address": mac["address"],
                    "interface": interface.id
                })
            new_macs.append(mac_obj.id)
        interface.update({"mac_addresses": new_macs}) 
        
    def sync_ip_addresses(self, interface, ip_addresses):
        for ip in ip_addresses:
            netbox_ips = self.slave_conn.ipam.ip_addresses.filter(address=ip)
            if not netbox_ips:
                query_params = {
                    "address": ip.address,
                    "status": "active",
                    "assigned_object_type": "dcim.interface",
                    "assigned_object_id": interface.id,
                    "tenant": 66,
                    "vrf": {"name": ip.vrf["name"]} if ip.vrf else None,
                }

                netbox_ip = self.slave_conn.ipam.ip_addresses.create(**query_params)
                return

            netbox_ip = list(netbox_ips)[0]
            # If IP exists in anycast
            if netbox_ip.role and netbox_ip.role.label == "Anycast":
                unassigned_anycast_ip = [x for x in netbox_ips if x.interface is None]
                assigned_anycast_ip = [
                    x for x in netbox_ips if x.interface and x.interface.id == interface.id
                ]
                # use the first available anycast ip
                if len(unassigned_anycast_ip):
                    netbox_ip = unassigned_anycast_ip[0]
                    netbox_ip.interface = interface
                    netbox_ip.save()
                # or if everything is assigned to other servers
                elif not len(assigned_anycast_ip):
                    query_params = {
                        "address": ip,
                        "status": "active",
                        "role": "Anycast",
                        "assigned_object_type": "dcim.interface",
                        "assigned_object_id": interface.id,
                    }
                    netbox_ip = self.slave_conn.ipam.ip_addresses.create(**query_params)
                return netbox_ip
            else:                
                netbox_ip.assigned_object_type = "dcim.interface"
                netbox_ip.assigned_object_id = interface.id
                netbox_ip.save()