def record_download(Device, device_id):
    device = Device.objects.get(pk=device_id)
    device.downloads += 1
    device.save()
    return device.downloads
