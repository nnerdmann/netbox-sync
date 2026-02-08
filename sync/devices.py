from sync.sync import Sync

class Devices(Sync): 
   
    api_object = "dcim.devices"
    sync_parameters = ["name", "site", "role", "device_type", "status", "serial", "rack", "location", "position", "face", "platform"]
    unique_parameter = ["name"]
   
    def post_create(self, oldobj, newobj):
        newobj = super().post_create(oldobj,newobj)
        # Remove all interfaces and power ports created by default
        for interface in self.slave_conn.dcim.interfaces.filter(device_id=newobj.id):
            interface.delete()
        for power_port in self.slave_conn.dcim.power_ports.filter(device_id=newobj.id):
            power_port.delete()
        return newobj
