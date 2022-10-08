def getConfig():
    config = type(
        "Config",
        (object,),
        {
            "IotEndpoint": "https://",
        },
    )

    return config
