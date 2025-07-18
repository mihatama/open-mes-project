from django.db import models
from uuid6 import uuid7

# Create your models here.

class Machine(models.Model):
    """設備マスター"""
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    machine_number = models.CharField(max_length=50, unique=True, verbose_name="設備番号")
    name = models.CharField(max_length=255, verbose_name="設備名")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="設置場所")
    description = models.TextField(blank=True, null=True, verbose_name="説明")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine_number} - {self.name}"

    class Meta:
        verbose_name = "設備"
        verbose_name_plural = "設備"
        ordering = ['machine_number']
