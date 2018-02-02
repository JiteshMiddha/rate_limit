from django.db import models
from model_utils.models import TimeStampedModel, MonitorField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from django.contrib.postgres.fields import JSONField


# Create your models here.
from rate_limit.constants import SpecializationType


class ClientRateLimitConfig(models.Model):

    client_id = models.CharField(max_length=255, unique=True, db_index=True)
    specialization = models.CharField(max_length=10, choices=SpecializationType.choices,
                                      validators=[SpecializationType.validator])
    end_point = models.TextField(null=True)
    # By default the values will be set to -1 (indicating no-limit)
    limit_sec = models.IntegerField(default=-1)
    limit_min = models.IntegerField(default=-1)
    limit_hour = models.IntegerField(default=-1)
    limit_week = models.IntegerField(default=-1)
    limit_month = models.IntegerField(default=-1)
    #
    created = AutoCreatedField('created')
    modified = AutoLastModifiedField('modified')

    class Meta:
        app_label = 'rate_limit'
        db_table = 'client_rate_limit_config'

    @classmethod
    def rate_limit_new_client(cls):
        client_id = "CLIENT_1"
        data = dict(client_id="CLIENT_1",
                    global_limit={

                    },
                    end_point=""
                    )
        cls.objects.create()



