import datetime

def log(event, *args, **kwargs):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    print("{} {}".format(timestamp, event), *args, **kwargs)
