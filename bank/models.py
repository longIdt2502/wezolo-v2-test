from django.db import models


class Banks(models.Model):
    class Meta:
        verbose_name = "Banks"
        db_table = "banks"

    code = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    bin_code = models.CharField(max_length=10, null=False, blank=False)
    short_name = models.CharField(max_length=50, null=False, blank=False)
    logo = models.CharField(max_length=200, null=True, blank=True)
    transfer_supported = models.BooleanField(null=True)
    lookup_supported = models.BooleanField(null=True)
    support = models.IntegerField(null=True)
    is_transfer = models.BooleanField(null=True)
    swift_code = models.CharField(max_length=11, null=True, blank=True)
