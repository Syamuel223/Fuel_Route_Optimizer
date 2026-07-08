from django.db import models


class FuelStation(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=6, decimal_places=5)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geocoded = models.BooleanField(default=False)
    source_row = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['state', 'city']),
            models.Index(fields=['price']),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.city}, {self.state}"
