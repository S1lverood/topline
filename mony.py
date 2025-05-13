# pip install yoomoney==0.1.0
import requests
from yoomoney import Authorize

redirect_url = "https://t.me/toplinevipbot"
client_id = "4A6F26767DF28FD85A0C532FA235591FCE2CBFFC85289E4A2F2DA99A201A1FB7"


def authorize_m(client_id, redirect_uri):
    Authorize(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=[
            "account-info",
            "operation-history",
            "operation-details",
            "incoming-transfers",
            "payment-p2p",
            "payment-shop"
        ]
    )


authorize_m(client_id, redirect_url)
