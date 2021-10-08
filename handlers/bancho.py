from xevel import Router, Request
from geoip2 import database
from typing import Union

from constants.privileges import Privileges, ClientPrivileges
from utils.general import now, now_float, make_safe
from utils.password import encrypt_password
from objects.player import Player
from constants.general import *
from utils.logging import *
from packets import writer
from objects import glob
from . import packets

import uuid

bancho_router = Router({
    f'c.{glob.config.serving_domain}',
    f'c4.{glob.config.serving_domain}',
    f'ce.{glob.config.serving_domain}'
})

geolocation_reader = database.Reader('ext/geoloc.mmdb')

def web_page() -> bytes:
    player_list = '\n'.join(p.name for p in glob.players.online)
    return (BASE_WEB_MESSAGE + player_list).encode()

@bancho_router.route("/", ["POST", "GET"])
async def bancho_client(request: Request) -> Union[tuple, bytes]:
    headers = request.headers

    if not (agent := headers.get("User-Agent")) or agent != "osu!" or request.type == "GET": return web_page()
    if not (token := headers.get('osu-token')): return await login(request)
    if not (player := glob.players.get(token=token)): return writer.restartServer(0)

    body = request.body
    packet_map = glob.packets if not player.disallowed else glob.restricted_packets

    if body[0] != 4:
        for packet, callback in packet_map.items():
            if body[0] == packet: 
                await callback(player, body)
                debug(f"Packet {packet.name} handled for {player.name}")

    player.last_ping = now()

    request.resp_headers['Content-Type'] = 'text/html; charset=UTF-8'
    return player.dequeue() or b''

async def login(request: Request) -> bytes:
    start = now_float()
    data = request.body

    if len(
        _info := data.decode().split('\n')[:-1]
    ) != 3:
        request.resp_headers['cho-token'] = 'no'
        return writer.userID(-2)

    if len(
        client_info := _info[2].split('|')
    ) != 5:
        request.resp_headers['cho-token'] = 'no'
        return writer.userID(-2)

    username = _info[0]
    client_md5 = _info[1].encode()

    if 'tourney' in client_info[0]: tourney_client = True
    else: tourney_client = False

    player = None
    if not tourney_client: player = glob.players.get(name=username, online=False)

    if not player:
        db_user = await glob.sql.fetchrow('SELECT * FROM users WHERE safe_name = %s', [make_safe(username)])
        if not db_user:
            debug(f"{username} does not exist")

            request.resp_headers['cho-token'] = 'no'
            return writer.userID(-1)

        db_user['country_iso'] = db_user['country'].upper()

        player = await Player.login(db_user)
        await player.set_stats()

        await glob.players.add_player(player)

    if not glob.password_cache.verify_password(client_md5, encrypt_password(player.encrypted_password)):
            debug(f"{username} provided an incorrect password")
            request.resp_headers['cho-token'] = 'no'
            return writer.userID(-1)

    if player.banned:
        request.resp_headers['cho-token'] = 'no'
        return writer.userID(-3)

    if 'CF-Connecting-IP' in request.headers: ip = request.headers['CF-Connecting-IP']
    elif 'X-Forwarded-For' in request.headers: ip = request.headers['X-Forwarded-For']
    elif 'X-Real-IP' in request.headers: ip = request.headers['X-Real-IP']

    if not (geoloc := glob.geoloc_cache.get(ip)):
        geoloc = geolocation_reader.city(ip)
        glob.geoloc_cache.add(ip, geoloc)

    player.loc[1], player.loc[0] = (
        geoloc.location.latitude,
        geoloc.location.longitude
    )

    if player.country_iso.upper() == 'XX':
        player.country_iso = geoloc.country.iso_code.upper()
        await glob.db.execute("UPDATE users SET country = %s WHERE id = %s", [player.country_iso.lower(), player.id])

    player.tourney_client = tourney_client
    if player.tourney_client and not player.priv & Privileges.Tourney:
        request.resp_headers['cho-token'] = 'no'
        return writer.userID(-1)

    # anticheat tm

    if (player_online := glob.players.get(id=player.id)) and (start - player_online.last_ping) > 10 and not player.tourney_client: player_online.logout()

    token = uuid.uuid4()
    player.utc_offset = int(client_info[1])
    player.token = str(token)
    player.login_time = now()
    player.password_md5 = client_md5.decode()
    player.online = True

    data = bytearray(writer.userID(player.id))
    data += writer.protocolVersion(19)
    data += writer.banchoPrivileges(player.client_priv | ClientPrivileges.Supporter)
    data += writer.userPresence(player) + writer.userStats(player)
    data += writer.channelInfoEnd()
    data += writer.menuIcon()
    data += writer.friends(player.friends)
    data += writer.silenceEnd(player.silence_end)

    if not player.priv & Privileges.Verified: 
        if player.id == 3: await player.set_priv(Privileges.Master)
        else: await player.add_priv(Privileges.Verified)

        info(f"{player.name} verified their account")
    
        player.receive_message(
            WELCOME_MSG,
            glob.bot
        )

    for channel in glob.channels:
        if channel.auto_join: player.join_channel(channel)
        data += writer.channelInfo(channel)

    if not player.restricted: glob.players.enqueue(writer.userPresence(player) + writer.userStats(player))
    for o in glob.players.online: data += writer.userPresence(o) + writer.userStats(o)

    if player.clan: player.join_channel(player.clan.channel)
    if player.restricted: player.receive_message(RESTRICTED_MSG, glob.bot)
    elif player.frozen: player.receive_message(FROZEN_MSG, glob.bot)

    elapsed = (now_float() - start) * 1000
    data += writer.notification(f'Welcome to astrid!\n\nTime Elapsed: {elapsed:.2f}ms')
    info(f'{player.name} logged in (Time Elapsed: {elapsed:.2f}ms)')

    request.resp_headers['cho-token'] = token
    request.resp_headers['Pragma'] = 'no-cache'
    request.resp_headers['Cache-Control'] = 'no-cache'

    return bytes(data)
    



    