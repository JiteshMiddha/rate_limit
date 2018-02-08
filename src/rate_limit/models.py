__author__ = 'sanjeev'
from django.db import models, transaction, connection
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from rate_limit.constants import SpecializationType


class ClientRateLimitConfig(models.Model):
    client_id = models.CharField(max_length=255, db_index=True)
    specialization = models.CharField(max_length=10, choices=SpecializationType.choices,
                                      validators=[SpecializationType.validator])
    http_method = models.CharField(max_length=10, null=True)
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
    def fetch_all_config(cls):
        # sql query to fetch configuration
        sql = """
              SELECT b.client_id,
                        array_to_json(array_agg(jsonb_build_object('specialization', b.specialization,
                                          'limit', b.limits))) AS config
              FROM (SELECT client_id, specialization,
                        array_to_json(array_agg(
                                    jsonb_build_object(
                                        'http_method', http_method,
                                        'end_point', end_point,
                                        'limit', jsonb_build_object('SEC', limit_sec, 'MIN', limit_min,
                                                'HOUR', limit_hour, 'WEEK', limit_week, 'MONTH', limit_month)
                                    )
                                )
                        ) as limits
                      FROM client_rate_limit_config
                      GROUP by client_id, specialization) b
              GROUP by b.client_id
        """
        cursor = connection.cursor()
        cursor.execute(sql)
        all_client_configs = cursor.fetchall()
        if not all_client_configs:
            return []
        all_configs = {}
        for cl_config in all_client_configs:
            # Make final configuration key-value pair to store in REDIS
            client_id = cl_config[0].upper()
            configs = cl_config[1]
            final_config = {}
            for conf in configs:
                if conf["specialization"] == "GLOBAL":
                    db_cfg = conf["limit"][0]["limit"]
                    f_conf = {}
                    [f_conf.update({k: v}) for k, v in db_cfg.items() if (v is not None and v > 0)]
                    key_name = "{0}:S:GLOBAL".format(client_id)
                    final_config[key_name] = f_conf
                if conf["specialization"] == "METHOD":
                    for _ in conf["limit"]:
                        db_cfg = _["limit"]
                        f_conf = {}
                        [f_conf.update({k: v}) for k, v in db_cfg.items() if (v is not None and v > 0)]
                        key_name = "{0}:S:METHOD:{1}".format(client_id, _["http_method"].upper())
                        final_config[key_name] = f_conf
                if conf["specialization"] == "API":
                    for _ in conf["limit"]:
                        db_cfg = _["limit"]
                        f_conf = {}
                        [f_conf.update({k: v}) for k, v in db_cfg.items() if (v is not None and v > 0)]
                        key_name = "{0}:S:API:{1}".format(client_id, _["end_point"].upper())
                        final_config[key_name] = f_conf
            all_configs["client_id"] = final_config
        return all_configs

    @classmethod
    def create_rate_limit_entry(cls, rate_limit_config):
        window_and_respective_column = {"SEC": "limit_sec", "MIN": "limit_min", "HOUR": "limit_hour",
                                        "WEEK": "limit_week", "MONTH": "limit_month"}
        if not rate_limit_config:
            return
        with transaction.atomic():
            for d in rate_limit_config:
                client_id = d["client_id"].upper()
                if d.get("global_limit"):
                    ins = cls(client_id=client_id, specialization=SpecializationType.GLOBAL)
                    g_limit = d["global_limit"]
                    [setattr(ins, window_and_respective_column[k], int(v)) for k, v in g_limit.items() if v]
                    ins.save()
                if d.get("method_limits"):
                    for met in d["method_limits"]:
                        ins = cls(client_id=client_id, specialization=SpecializationType.METHOD, http_method=met["http_method"].upper())
                        limit = met["limit"]
                        [setattr(ins, window_and_respective_column[k], int(v)) for k, v in limit.items() if v]
                        ins.save()
                if d.get("end_point"):
                    for met in d["end_point"]:
                        ins = cls(client_id=client_id, specialization=SpecializationType.API, end_point=met["url"].upper())
                        limit = met["limit"]
                        [setattr(ins, window_and_respective_column[k], int(v)) for k, v in limit.items() if v]
                        ins.save()
