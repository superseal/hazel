import re
from .game_consts import HIT_ZONE, HIT_ITEM, DEATH_CAUSE, WORLD_NUM

def parse_event(raw_line):
    # Separate event name from args
    split_line = raw_line.lstrip(" ").rstrip("\n").split(" ", 2)
    event = split_line[1].rstrip(":")

    if len(split_line) > 2:
        raw_args = split_line[2]
        return (event, raw_args)
    else:
        return (event, "")

def parse_args(event, raw_args):
    # ClientUserinfo contains an IP and a port, keep the colon
    # The colon is useless in other commands
    if event != "ClientUserinfo":
        raw_args = raw_args.replace(":", "")

    # Actual parsing
    if event == "InitGame":
        # Partition arguments into tuples
        raw_args = raw_args.lstrip(" ").split("\\")
        raw_args = [raw_args[i:i + 2] for i in range(1, len(raw_args), 2)]

        var_names = ("mapname", "g_gametype", "fraglimit", "timelimit")
        cvars = {cvar: cvalue for (cvar, cvalue) in raw_args if cvar in var_names}
        return [cvars[v] for v in var_names]

    elif event in ("ShutdownGame", "Exit"):
        return None

    elif event in ("ClientConnect", "ClientDisconnect", "ClientBegin", "ClientSpawn"):
        player_num = int(raw_args)
        return player_num

    elif event == "ClientUserinfo":
        num = int(raw_args.split()[0])
        # Partition arguments into tuples
        raw_args = raw_args.split("\\")
        raw_args = [raw_args[i:i + 2] for i in range(1, len(raw_args), 2)]

        var_names = ("ip", "name", "gear")
        cvars = {cvar: cvalue for (cvar, cvalue) in raw_args if cvar in var_names}
        # Remove color codes
        cvars["name"] = re.sub(r"\^\d", "", cvars["name"])
        # Strip port from IP address
        cvars["ip"] = cvars["ip"].split(":")[0]

        # gear cvar is only in the second ClientUserinfo
        if "gear" in cvars:
            return [num] + [cvars[v] for v in var_names]
        else:
            return [num] + [cvars["ip"], cvars["name"], "A"]

    elif event == "ClientUserinfoChanged":
        num = int(raw_args.split()[0])
        name = raw_args.split("\\")[1]
        return [num, name]
    
    elif event == "Kill":
        killer_num, victim_num, cause, message = raw_args.split(" ", 3)
        killer_num, victim_num, cause = int(killer_num), int(victim_num), int(cause)
        
        cause = DEATH_CAUSE[cause]
        if '<world>' in message or cause in ["MOD_FALLING", "MOD_WATER", "MOD_LAVA", "MOD_TRIGGER_HURT"]:
            killer_num = WORLD_NUM

        return [killer_num, victim_num, cause]

    elif event == "Hit":
        victim_num, attacker_num, zone, weapon, message = raw_args.split(" ", 4)
        victim_num, attacker_num, zone, weapon = int(victim_num), int(attacker_num), int(zone), int(weapon)
        
        zone = HIT_ZONE[zone]
        weapon = HIT_ITEM[weapon]
        return [attacker_num, victim_num, zone, weapon]

    elif event == "say":
        player_num, player_name, message = raw_args.split(" ", 2)
        player_num = int(player_num)

        return [player_num, message]

    elif event in ("restart", "map_restart"):
        return None
    
    # Bot commands
    elif event == ".":
        command_name, command_args = raw_args.split(" ", 1)
        return [command_name, command_args]

def parse_line(raw_line):
    event, raw_args = parse_event(raw_line)
    args = parse_args(event, raw_args)
    return (event, args)
