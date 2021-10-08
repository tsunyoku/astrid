from constants.privileges import Privileges
from packets.reader import handle_packet
from constants.types import osuTypes
from constants.modes import lbModes
from objects.player import Player
from constants.mods import Mods
from utils.logging import info
from utils.general import now
from packets.writer import *
from objects import glob

def packet(packet: Packets, restricted_packet: bool = False):
    """Decorator to add a packet handler to the scope"""

    def wrapper(callback):
        glob.packets |= {packet: callback}
        if restricted_packet: glob.restricted_packets |= {packet: callback}

    return wrapper

"""
Below contains all the functions responsible for handling packets the osu! client may send to the server.
If you are looking for where these will be called, check endpoints/bancho.py.
"""

@packet(Packets.OSU_REQUEST_STATUS_UPDATE, restricted_packet=True)
async def update_stats(p: Player, packet: bytes) -> None: return p.enqueue(userStats(p))

@packet(Packets.OSU_USER_STATS_REQUEST, restricted_packet=True)
async def stats_request(p: Player, packet: bytes) -> None:
    user_ids = handle_packet(packet, (osuTypes.i32_list,))

    for user in glob.players.unrestricted:
        if user.id != p.id and user.id in user_ids: p.enqueue(userStats(user))

@packet(Packets.OSU_USER_PRESENCE_REQUEST)
async def presence_request(p: Player, packet: bytes) -> None:
    user_ids = handle_packet(packet, (osuTypes.i32_list,))

    for user in glob.players.unrestricted:
        if user.id != p.id and user.id in user_ids: p.enqueue(userPresence(user))

@packet(Packets.OSU_USER_PRESENCE_REQUEST_ALL)
async def full_presence_request(p: Player, packet: bytes) -> None:
    for user in glob.players.online:
        if user.id != p.id: p.enqueue(userPresence(user))

@packet(Packets.OSU_FRIEND_ADD)
async def add_friend(p: Player, packet: bytes) -> None:
    target = handle_packet(packet, (osuTypes.i32,))

    if target in p.friends: return
    p.friends.append(target)

    await glob.sql.execute("INSERT INTO friends (user1, user2) VALUES (%s, %s)", [p.id, target])
    info(f"{p.name} added user ID {target} into their friends list.")

@packet(Packets.OSU_FRIEND_REMOVE)
async def remove_friend(p: Player, packet: bytes) -> None:
    target = handle_packet(packet, (osuTypes.i32,))

    if target not in p.friends: return
    p.friends.remove(target)

    await glob.sql.execute("DELETE FROM friends WHERE user1 = %s AND user2 = %s", [p.id, target])
    info(f"{p.name} removed user ID {target} from their friends list.")

@packet(Packets.OSU_LOGOUT, restricted_packet=True)
async def logout(p: Player, packet: bytes) -> None:
    if (now() - p.login_time) < 1: return
    p.logout()

@packet(Packets.OSU_SEND_PRIVATE_MESSAGE)
async def send_dm(p: Player, packet: bytes) -> None:
    msg_data = handle_packet(packet, (osuTypes.message,))

    if not (target := glob.players.get(name=msg_data.target_username)): return

    # TODO: handle /np, commands

    target.receive_message(msg_data.msg, p)
    info(f"{p.name} sent \"{msg_data.msg}\" to {target.name}")

@packet(Packets.OSU_SEND_PUBLIC_MESSAGE)
async def send_msg(p: Player, packet: bytes) -> None:
    msg_data = handle_packet(packet, (osuTypes.message,))

    # TODO: handle multi

    if msg_data.target_username == "#clan":
        if not p.clan: return
        channel = p.clan.channel
    elif msg_data.target_username not in ("#highlight", "#userlog"): channel = glob.channels.get(msg_data.target_username)

    if not channel: return
    channel.send(p, msg_data.msg)

@packet(Packets.OSU_CHANNEL_JOIN)
async def join_channel(p: Player, packet: bytes) -> None:
    channel_name = handle_packet(packet, (osuTypes.string,))

    # TODO: handle multi

    if channel_name == "#spectator":
        if p.spectating: user_id = p.spectating.id
        elif p.spectators: user_id = p.id
        else: return

        channel = glob.channels.get(f"#spec_{user_id}")
    elif channel_name == "#clan":
        if not p.clan: return
        channel = p.clan.channel
    else: channel = glob.channels.get(channel_name)

    if not channel: return
    p.join_channel(channel)

@packet(Packets.OSU_CHANNEL_PART)
async def leave_channel(p: Player, packet: bytes) -> None:
    channel_name = handle_packet(packet, (osuTypes.string,))

    # TODO: handle multi

    if channel_name in ("#highlight", "#userlog") or channel_name[0] != "#": return
    if channel_name == "#spectator":
        if p.spectating: user_id = p.spectating.id
        elif p.spectators: user_id = p.id
        else: return

        channel = glob.channels.get(f"#spec_{user_id}")
    elif channel_name == "#clan":
        if not p.clan: return
        channel = p.clan.channel
    else: channel = glob.channels.get(channel_name)

    if not channel or p not in channel.players: return

    p.leave_channel(channel)

@packet(Packets.OSU_CHANGE_ACTION, restricted_packet=True)
async def action_update(p: Player, packet: bytes) -> None:
    action, action_info, map_md5, mods, mode, map_id = handle_packet(
        packet,
        (
            osuTypes.u8,
            osuTypes.string,
            osuTypes.string,
            osuTypes.u32,
            osuTypes.u8,
            osuTypes.i32
        )
    )

    if action == 0 and mods & Mods.RELAX: action_info = "on Relax"
    elif action == 0 and mods & Mods.AUTOPILOT: action_info = "on Autopilot"

    p.action = action
    p.action_info = action_info
    p.map_md5 = map_md5
    p.mods = Mods(mods)
    p.mode = lbModes(mode, mods)
    p.map_id = map_id

    if p.action == 2: p.action_info += " +" + repr(p.mods)
    if not p.disallowed: glob.players.enqueue(userStats(p))

@packet(Packets.OSU_START_SPECTATING)
async def start_spectating(p: Player, packet: bytes) -> None:
    target_id = handle_packet(packet, (osuTypes.i32,))

    if target_id == 1 or not (target := glob.players.get(id=target_id)): return
    target.add_spectator(p)

@packet(Packets.OSU_STOP_SPECTATING)
async def stop_spectating(p: Player, packet: bytes) -> None:
    if not (host := p.spectating): return
    host.remove_spectator(p)

@packet(Packets.OSU_SPECTATE_FRAMES)
async def spectator_Frames(p: Player, packet: bytes) -> None:
    frames = handle_packet(packet, (osuTypes.raw,))
    frames_packet = spectateFrames(frames)
    for u in p.spectators: u.enqueue(frames_packet)

# TODO: multi handlers
