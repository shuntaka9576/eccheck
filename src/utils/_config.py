def getConfig():
    config = type(
        "Config",
        (object,),
        {
            # FQDNのみでOK
            "IotEndpoint": "xxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com",
        },
    )

    return config
