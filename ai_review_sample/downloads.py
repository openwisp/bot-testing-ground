from django.db.models import F


def record_download(Device, device_id):
    Device.objects.filter(pk=device_id).update(downloads=F("downloads") + 1)
    return Device.objects.values_list("downloads", flat=True).get(pk=device_id)
