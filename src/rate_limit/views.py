import json
from django.http import HttpResponse


def get_status(request):
    """
    API: GET /status/
    Sample API view to get status
    :param request:
    :return:
    """
    data = {"status": "ACTIVE"}
    return HttpResponse(json.dumps(data), status=200)


def initiate_payment(request):
    """
    API: POST /pay/
    Sample API view to initiate payment
    :param request:
    :return:
    """
    data = {"txn_id": "1cf91ea8-d8c2-4437-8453-f839e465d263",
            "txn_status": "INITIATED",
            "txn_amt": 5000}
    return HttpResponse(json.dumps(data), status=202)

