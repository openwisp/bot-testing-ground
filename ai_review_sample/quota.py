def reserve_quota(Organization, org_id, amount):
    org = Organization.objects.get(pk=org_id)
    if org.used + amount > org.limit:
        raise ValueError("Quota exceeded")
    org.used += amount
    org.save(update_fields=["used"])
    return org.limit - org.used
