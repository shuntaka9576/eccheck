def getConfig():
    config = type(
        "Config",
        (object,),
        {
            "IotEndpoint": "https://xxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com",
        },
    )

    return config
