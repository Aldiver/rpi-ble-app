import dbus

from ble_core.advertisement import Advertisement
from ble_core.service import Application, Service, Characteristic, Descriptor
# from gpiozero import CPUTemperature

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class SensorAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Raspberry Pi 0") 
        self.include_tx_power = True

class RaspberryService(Service):
    RASPBERRY_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.RASPBERRY_SVC_UUID, True)
        self.add_characteristic(OutboundCharacteristic(self, "00000002-710e-4a5b-8d75-3e5b444bc3cf", ["read", "notify"]))
        self.add_characteristic(OutboundCharacteristic(self, "00000003-710e-4a5b-8d75-3e5b444bc3cf", ["read", "notify"]))
        self.add_characteristic(OutboundCharacteristic(self, "00000004-710e-4a5b-8d75-3e5b444bc3cf", ["read", "notify"]))
        self.add_characteristic(OutboundCharacteristic(self, "00000005-710e-4a5b-8d75-3e5b444bc3cf", ["read", "notify"]))
        self.add_characteristic(InboundCharacteristic(self, "00000006-710e-4a5b-8d75-3e5b444bc3cf", ["read", "write"]))

    def is_farenheit(self):
        return self.farenheit

    def set_farenheit(self, farenheit):
        self.farenheit = farenheit

class OutboundCharacteristic(Characteristic):

    def __init__(self, service, uuid, flags):
        if "notify" in flags:
            self.notifying = False
        else:
            self.notifying = True

        Characteristic.__init__(
                self, service, uuid,
                flags)
        self.add_descriptor(RaspberryDescriptor(self, "2901", "Temperature Descriptor", self.flags))

    def get_sensor_value(self):
        value = []
        temp = 100
        strtemp = str(round(temp, 1))
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_temperature_callback(self):
        if self.notifying:
            value = self.get_sensor_value()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_sensor_value()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_temperature_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        print("read")
        value = self.get_sensor_value()

        return value

class InboundCharacteristic(Characteristic):

    def __init__(self, service, uuid, flags):
        Characteristic.__init__(
                self, uuid,
                flags, service)
        self.add_descriptor(RaspberryDescriptor(self, "2901", "Alert Descriptor", self.flags))

    def WriteValue(self, value, options):
        val = str(value[0]).upper()
        print(val)

    def ReadValue(self, options):
        value = []
        #not implemented
        return value

class RaspberryDescriptor(Descriptor):
    def __init__(self, characteristic, uuid, description, flags):
        Descriptor.__init__(
                self, uuid,
                flags,
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.description

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(RaspberryService(0))
app.register()

adv = SensorAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
