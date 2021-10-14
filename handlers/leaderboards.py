from typing import Optional

from constants.general import BASE_HEADER, LEADERBOARD_BASE, COUNT_QUERY, PB_BASE, PB_COUNT
from caching.caches import get_lb_cache, get_pb_cache, add_lb_cache, add_pb_cache
from constants.privileges import Privileges
from objects.beatmap import Beatmap
from objects.player import Player
from objects import glob

def format_score(score: dict, clan: bool) -> bytes:
    score, rank = score
    name = score['name']
    if clan:
        user = glob.players.get(id=int(score['uid']), online=False)
        
        try: 
            if user.clan: name = f"[{user.clan.tag}] " + user.name
        except AttributeError:
            pass # can happen if a lb is requested before players get cached, we can safely ignore this

    return (
        f"{score['id']}|{name}|{int(score['sort'])}|{score['combo']}|{score['n50']}|{score['n100']}|{score['n300']}|"
        f"{score['miss']}|{score['katu']}|{score['geki']}|{score['fc']}|{score['mods']}|"
        f"{score['uid']}|{rank}|{score['time']}|1"
    )

async def get_best(user: Player, _map: Beatmap, leaderboard: tuple, lb_type: int) -> list:
    if cached_pb := get_pb_cache(user.mode, _map.md5, lb_type, user.mods, user): return cached_pb

    db_pb = db_place = None

    # attempt to use current scores to find db
    for idx, _score in enumerate(leaderboard):
        if int(_score["uid"]) == user.id:
            db_pb, db_place = _score, idx + 1
            break
    else:
        if len(leaderboard) < 100: return None # if it isnt the top 100 we just checked, and the size is less than 100, it cannot exist

        where_args = " AND ".join((
            "s.md5 = %s",
            "s.mode = %s",
            "s.status = 2",
            f"u.id = %s",
        ))

        where_vals = (
            map.md5,
            user.mode.as_vn,
            user.id,
        )

        if lb_type == 2: # selected-mods
            where_args += " AND s.mods = %s"
            where_vals += (user.mods.value,)

        db_query = PB_BASE.format(
            sort=user.mode.sort,
            table=user.mode.table,
            where_args=where_args,
        )

        db_pb = await glob.sql.fetchrow(db_query, where_vals)
        if not db_pb: return None

        place_args = " AND ".join((
            "s.md5 = %s",
            "s.mode = %s",
            "s.status = 2",
            f"s.pp > {db_pb['pp']}",
            f"NOT u.priv & {Privileges.Disallowed}"
        ))
        
        pb_query = PB_COUNT.format(
            sort=user.mode.sort,
            table=user.mode.table,
            where_args=place_args
        )

        db_place = int(await glob.sql.fetchval(pb_query, where_vals[:2]))

    add_pb_cache(user.mode, _map.md5, lb_type, db_pb, db_place, user.mods, user)
    return db_pb, db_place

async def format_lb(_map: Beatmap, user: Player, leaderboard: tuple, lb_type: int) -> bytes:
    base_leaderboard = BASE_HEADER.format(map=_map, count=leaderboard[1])

    if (personal_best := await get_best(user, _map, leaderboard[0], lb_type)): base_leaderboard += f"\n{format_score(personal_best, clan=False)}"
    else: base_leaderboard += "\n"

    for idx, score in enumerate(leaderboard[0]): 
        base_leaderboard += f"\n{format_score((score, idx + 1), clan=int(score['uid']) != user.id)}"

    return base_leaderboard.encode()

async def fetch_leaderboard(_map: Beatmap, user: Player, lb_type: int) -> bytes:
    if cached_lb := get_lb_cache(user.mode, _map.md5, lb_type, user.mods, user): 
        return await format_lb(_map, user, cached_lb, lb_type)

    where_args = " AND ".join((
        "s.md5 = %s",
        "s.mode = %s",
        "s.status = 2",
        f"NOT u.priv & {Privileges.Disallowed}",
    ))

    where_vals = (
        _map.md5,
        user.mode.as_vn,
    )

    if lb_type == 2: # selected-mods
        where_args += " AND s.mods = %s"
        where_vals += (user.mods.value,)
    elif lb_type == 3: # friends lb
        friend_list = ", ".join(map(str, user.friends + [str(user.id)]))
        where_args += f" AND s.uid IN ({friend_list})"
    elif lb_type == 4: # country lb
        where_args += " AND u.country = %s"
        where_vals += (user.country_iso.lower(),)

    db_query = LEADERBOARD_BASE.format(
        sort=user.mode.sort,
        table=user.mode.table,
        where_args=where_args
    )

    db_scores = await glob.sql.fetch(db_query, where_vals)

    count = len(db_scores)
    count_query = COUNT_QUERY.format(
        table=user.mode.table,
        where_args=where_args
    )

    if count == 100: count = int(await glob.sql.fetchval(count_query, where_vals))

    add_lb_cache(user.mode, _map.md5, lb_type, db_scores, count, user.mods, user)
    return await format_lb(_map, user, (db_scores, count,), lb_type)