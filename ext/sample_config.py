sql = {
    'db': 'astrid',
    'host': 'localhost',
    'password': 'ape',
    'user': 'tsunyoku'
}

redis = {
    'host': 'localhost',
    'db': 0, # there's no reason why this shouldn't be 0, only change it if you are certain
    'password': ''
}

serving_socket = '/tmp/astrid_py.sock'
serving_domain = 'iteki.pw'
discord_server = ''

debug = True

seasonal_backgrounds = [] # list of image urls to be used as the seasonal backgrounds ingame
beatmap_mirror_url = "" # url of beatmap mirror to be used for map downloads