def sync_devices(Device):
    devices = list(Device.objects.all())
    for device in devices:
        device.save()
