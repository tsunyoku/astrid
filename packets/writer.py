import struct

from enum import IntEnum

from constants.osu_types import osuTypes
from objects import glob

class Packets(IntEnum):
    OSU_CHANGE_ACTION = 0
    OSU_SEND_PUBLIC_MESSAGE = 1
    OSU_LOGOUT = 2
    OSU_REQUEST_STATUS_UPDATE = 3
    OSU_PING = 4
    CHO_USER_ID = 5
    CHO_SEND_MESSAGE = 7
    CHO_PONG = 8
    CHO_HANDLE_IRC_CHANGE_USERNAME = 9
    CHO_HANDLE_IRC_QUIT = 10
    CHO_USER_STATS = 11
    CHO_USER_LOGOUT = 12
    CHO_SPECTATOR_JOINED = 13
    CHO_SPECTATOR_LEFT = 14
    CHO_SPECTATE_FRAMES = 15
    OSU_START_SPECTATING = 16
    OSU_STOP_SPECTATING = 17
    OSU_SPECTATE_FRAMES = 18
    CHO_VERSION_UPDATE = 19
    OSU_ERROR_REPORT = 20
    OSU_CANT_SPECTATE = 21
    CHO_SPECTATOR_CANT_SPECTATE = 22
    CHO_GET_ATTENTION = 23
    CHO_NOTIFICATION = 24
    OSU_SEND_PRIVATE_MESSAGE = 25
    CHO_UPDATE_MATCH = 26
    CHO_NEW_MATCH = 27
    CHO_DISPOSE_MATCH = 28
    OSU_PART_LOBBY = 29
    OSU_JOIN_LOBBY = 30
    OSU_CREATE_MATCH = 31
    OSU_JOIN_MATCH = 32
    OSU_PART_MATCH = 33
    CHO_TOGGLE_BLOCK_NON_FRIEND_DMS = 34
    CHO_MATCH_JOIN_SUCCESS = 36
    CHO_MATCH_JOIN_FAIL = 37
    OSU_MATCH_CHANGE_SLOT = 38
    OSU_MATCH_READY = 39
    OSU_MATCH_LOCK = 40
    OSU_MATCH_CHANGE_SETTINGS = 41
    CHO_FELLOW_SPECTATOR_JOINED = 42
    CHO_FELLOW_SPECTATOR_LEFT = 43
    OSU_MATCH_START = 44
    CHO_ALL_PLAYERS_LOADED = 45
    CHO_MATCH_START = 46
    OSU_MATCH_SCORE_UPDATE = 47
    CHO_MATCH_SCORE_UPDATE = 48
    OSU_MATCH_COMPLETE = 49
    CHO_MATCH_TRANSFER_HOST = 50
    OSU_MATCH_CHANGE_MODS = 51
    OSU_MATCH_LOAD_COMPLETE = 52
    CHO_MATCH_ALL_PLAYERS_LOADED = 53
    OSU_MATCH_NO_BEATMAP = 54
    OSU_MATCH_NOT_READY = 55
    OSU_MATCH_FAILED = 56
    CHO_MATCH_PLAYER_FAILED = 57
    CHO_MATCH_COMPLETE = 58
    OSU_MATCH_HAS_BEATMAP = 59
    OSU_MATCH_SKIP_REQUEST = 60
    CHO_MATCH_SKIP = 61
    OSU_CHANNEL_JOIN = 63
    CHO_CHANNEL_JOIN_SUCCESS = 64
    CHO_CHANNEL_INFO = 65
    CHO_CHANNEL_KICK = 66
    CHO_CHANNEL_AUTO_JOIN = 67
    OSU_BEATMAP_INFO_REQUEST = 68
    CHO_BEATMAP_INFO_REPLY = 69
    OSU_MATCH_TRANSFER_HOST = 70
    CHO_PRIVILEGES = 71
    CHO_FRIENDS_LIST = 72
    OSU_FRIEND_ADD = 73
    OSU_FRIEND_REMOVE = 74
    CHO_PROTOCOL_VERSION = 75
    CHO_MAIN_MENU_ICON = 76
    OSU_MATCH_CHANGE_TEAM = 77
    OSU_CHANNEL_PART = 78
    OSU_RECEIVE_UPDATES = 79
    CHO_MATCH_PLAYER_SKIPPED = 81
    OSU_SET_AWAY_MESSAGE = 82
    CHO_USER_PRESENCE = 83
    OSU_IRC_ONLY = 84
    OSU_USER_STATS_REQUEST = 85
    CHO_RESTART = 86
    OSU_MATCH_INVITE = 87
    CHO_MATCH_INVITE = 88
    CHO_CHANNEL_INFO_END = 89
    OSU_MATCH_CHANGE_PASSWORD = 90
    CHO_MATCH_CHANGE_PASSWORD = 91
    CHO_SILENCE_END = 92
    OSU_TOURNAMENT_MATCH_INFO_REQUEST = 93
    CHO_USER_SILENCED = 94
    CHO_USER_PRESENCE_SINGLE = 95
    CHO_USER_PRESENCE_BUNDLE = 96
    OSU_USER_PRESENCE_REQUEST = 97
    OSU_USER_PRESENCE_REQUEST_ALL = 98
    OSU_TOGGLE_BLOCK_NON_FRIEND_DMS = 99
    CHO_USER_DM_BLOCKED = 100
    CHO_TARGET_IS_SILENCED = 101
    CHO_VERSION_UPDATE_FORCED = 102
    CHO_SWITCH_SERVER = 103
    CHO_ACCOUNT_RESTRICTED = 104
    CHO_MATCH_ABORT = 106
    CHO_SWITCH_TOURNAMENT_SERVER = 107
    OSU_TOURNAMENT_JOIN_MATCH_CHANNEL = 108
    OSU_TOURNAMENT_LEAVE_MATCH_CHANNEL = 109

def write_uleb128(length: int) -> bytearray:
    if length == 0: return bytearray(b"\x00")

    data = bytearray()
    shift = 0

    while length > 0:
        data.append(length & 0x7F)
        length >>= 7

        if length != 0: data[shift] |= 0x80
        shift += 1

    return data

def write_string(string: str) -> bytearray:
    if not string: return bytearray(b"\x00")

    data = bytearray(b"\x0B")

    encoded_string = string.encode("utf-8", "ignore")
    data += write_uleb128(len(encoded_string))
    data += encoded_string

    return data

def write_i32_list(_list: list) -> bytearray:
    data = bytearray(
        len(_list).to_bytes(2, "little")
    )

    for item in _list: data += item.to_bytes(4, 'little')
    return data

def write_message(args: tuple) -> bytearray:
    from_username, msg, target_username, from_id = args

    data = bytearray(
        write_string(from_username)
    )

    data += write_string(msg)
    data += write_string(target_username)
    data += from_id.to_bytes(
        4, 'little', signed = True
    )

    return data

def write_channel(args: tuple) -> bytearray:
    name, desc, players = args

    data = bytearray(
        write_string(name)
    )

    data += write_string(desc)
    data += players.to_bytes(2, 'little')

    return data

_spec = {
    osuTypes.i8: '<b',
    osuTypes.u8: '<B',
    osuTypes.i16: '<h',
    osuTypes.u16: '<H',
    osuTypes.i32: '<i',
    osuTypes.u32: '<I',
    osuTypes.f32: '<f',
    osuTypes.i64: '<q',
    osuTypes.u64: '<Q',
    osuTypes.f64: '<d'
}

_types = {
    osuTypes.string: write_string,
    osuTypes.i32_list: write_i32_list,
    osuTypes.message: write_message,
    osuTypes.channel: write_channel
}

def write(packet_id, *args) -> bytes:
    data = bytearray(
        struct.pack('<Hx', packet_id)
    )

    for _args, type in args:
        if type == osuTypes.raw: data += _args
        elif (func := _types.get(type)): data += func(_args)
        else: data += struct.pack(_spec[type], _args)

    data[3:3] = struct.pack("<I", len(data) - 3)
    return bytes(data)

def userID(id: int) -> bytes: return write(Packets.CHO_USER_ID, (id, osuTypes.i32))
def protocolVersion(version: int) -> bytes: return write(Packets.CHO_PROTOCOL_VERSION, (version, osuTypes.i32))
def banchoPrivileges(privilege: int) -> bytes: return write(Packets.CHO_PRIVILEGES, (privilege, osuTypes.i32))
def notification(msg: str) -> bytes: return write(Packets.CHO_NOTIFICATION, (msg, osuTypes.string))
def channelInfoEnd() -> bytes: return write(Packets.CHO_CHANNEL_INFO_END)
def restartServer(time: int) -> bytes: return write(Packets.CHO_RESTART, (time, osuTypes.i32))
def menuIcon() -> bytes: return write(Packets.CHO_MAIN_MENU_ICON, ('|', osuTypes.string))
def friends(friendsl) -> bytes: return write(Packets.CHO_FRIENDS_LIST, (friendsl, osuTypes.i32_list))
def silenceEnd(unix: int) -> bytes: return write(Packets.CHO_SILENCE_END, (unix, osuTypes.i32))
def sendMessage(fromname: str, msg: str, tarname: str, fromid: int) -> bytes: return write(Packets.CHO_SEND_MESSAGE, ((fromname, msg, tarname, fromid), osuTypes.message))
def logout(uid: int) -> bytes: return write(Packets.CHO_USER_LOGOUT, (uid, osuTypes.i32), (0, osuTypes.u8))
def blockDM() -> bytes: return write(Packets.CHO_USER_DM_BLOCKED)
def spectatorJoined(uid: int) -> bytes: return write(Packets.CHO_FELLOW_SPECTATOR_JOINED, (uid, osuTypes.i32))
def hostSpectatorJoined(uid: int) -> bytes: return write(Packets.CHO_SPECTATOR_JOINED, (uid, osuTypes.i32))
def spectatorLeft(uid: int) -> bytes: return write(Packets.CHO_FELLOW_SPECTATOR_LEFT, (uid, osuTypes.i32))
def hostSpectatorLeft(uid: int) -> bytes: return write(Packets.CHO_SPECTATOR_LEFT, (uid, osuTypes.i32))
def spectateFrames(frames: bytes) -> bytes: return write(Packets.CHO_SPECTATE_FRAMES, (frames, osuTypes.raw))
def channelJoin(chan: str) -> bytes: return write(Packets.CHO_CHANNEL_JOIN_SUCCESS, (chan, osuTypes.string))
def channelInfo(chan) -> bytes: return write(Packets.CHO_CHANNEL_INFO, ((chan.name, chan.desc, chan.player_count), osuTypes.channel))
def channelKick(chan: str) -> bytes: return write(Packets.CHO_CHANNEL_KICK, (chan, osuTypes.string))
def versionUpdateForced() -> bytes: return write(Packets.CHO_VERSION_UPDATE_FORCED)

def botPresence(player) -> bytes:
    return write(
        Packets.CHO_USER_PRESENCE,
        (player.id, osuTypes.i32),
        (player.name, osuTypes.string),
        (player.utc_offset + 24, osuTypes.u8), # utc offset
        (player.country, osuTypes.u8),
        (31, osuTypes.u8),
        (player.loc[0], osuTypes.f32), # long | off map cus bot
        (player.loc[1], osuTypes.f32), # lat | off map cus bot
        (0, osuTypes.i32)
    )

def userPresence(player) -> bytes:
    if player is glob.bot: return botPresence(player)

    return write(
        Packets.CHO_USER_PRESENCE,
        (player.id, osuTypes.i32),
        (player.name, osuTypes.string),
        (player.utc_offset + 24, osuTypes.u8),
        (player.country, osuTypes.u8),
        (player.client_priv.value | (player.mode_vn << 5), osuTypes.u8),
        (player.loc[0], osuTypes.f32),
        (player.loc[1], osuTypes.f32),
        (player.current_stats.rank, osuTypes.i32)
    )

def botStats() -> bytes:
    return write(
        Packets.CHO_USER_STATS,
        (1, osuTypes.i32),
        (6, osuTypes.u8),
        ('over astrid\'s code', osuTypes.string),
        ('', osuTypes.string),
        (0, osuTypes.i32),
        (0, osuTypes.u8),
        (0, osuTypes.i32),
        (0, osuTypes.i64),
        (0.00, osuTypes.f32),
        (0, osuTypes.i32),
        (0, osuTypes.i64),
        (0, osuTypes.i32),
        (0, osuTypes.i16)
    )

def userStats(player) -> bytes:
    if player is glob.bot: return botStats()

    return write(
        Packets.CHO_USER_STATS,
        (player.id, osuTypes.i32),
        (player.action, osuTypes.u8),
        (player.action_info, osuTypes.string),
        (player.map_md5, osuTypes.string),
        (player.mods.value, osuTypes.i32),
        (player.mode_vn, osuTypes.u8),
        (player.map_id, osuTypes.i32),
        (player.current_stats.rscore, osuTypes.i64),
        (player.current_stats.acc / 100.0, osuTypes.f32),
        (player.current_stats.pc, osuTypes.i32),
        (player.current_stats.tscore, osuTypes.i64),
        (player.current_stats.rank, osuTypes.i32),
        (player.current_stats.pp, osuTypes.i16)
    )