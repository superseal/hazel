import socket
import time
import re

import pygeoip
from game_vars import hit_zone, hit_item, death_cause

(ADDRESS, PORT) = ("192.155.94.108", 27960)
password = "testserver"

players = {}
stats = {}
first_kill, first_nade, first_knife = "", "", ""

ip_db = pygeoip.GeoIP("/home/urt/rcon_bot/pygeoip/GeoIP.dat")

def live_tail(log):
    log.seek(0, 2)
    while 1:
        line = log.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

def raw_command(cmd):
    time.sleep(0.2)
    message = b"\xff\xff\xff\xff" + ("%s\n" % cmd).encode("UTF-8")
    server.send(message)
    return server.recv(8096).replace(b"\xff\xff\xff\xff", b"").rstrip(b"\n")

def rcon(cmd):
    return raw_command("rcon {} {}".format(password, cmd))

####

def reset_stats():
    global first_kill, first_nade, first_knife, stats
    print("Resetting stats")
    first_kill, first_nade, first_knife = "", "", ""
    for key in stats.keys():
        stats[key] = [0, 0, 0]

def add_score(kill_type, killer_num):
    global stats

    if kill_type == "headshot":
        index = 0
        kill_type = "headshots"
    elif kill_type == "nade":
        index = 1
        kill_type = "nade kills"
    elif kill_type == "knife":
        index = 2
        kill_type = "knife kills"
    
    player_name = players[killer_num][0]
    points = stats[killer_num][index]
    points += 1
    stats[killer_num][index] += 1
    if (points % 5) == 0:
        rcon("say \"^4{} has {} {}\"".format(player_name, points, kill_type))
####

def parse_event(line):
    game_time, event, *raw_args = line.lstrip(" ").rstrip("\n").split(" ", 2)
    event = event.rstrip(":")
    # Flatten 
    if raw_args:
        raw_args = raw_args[0]
    else:
        raw_args = ""
    return game_time, event, raw_args

def parse_args(event, args):
    if event != "ClientUserinfo":
        args = args.replace(":", "")

    # players[x] = (name, score, address, ping)
    # stats[x] = [headshots, nade_kills, knife_kills]
    if event == "Kill":
        killer_num, victim_num, cause, message = args.split(" ", 3)
        killer_num = int(killer_num)
        victim_num = int(victim_num)
        cause = int(cause)
        cause = death_cause[cause]
        if '<world>' in message or cause in ["MOD_FALLING", "MOD_WATER", "MOD_LAVA", "MOD_TRIGGER_HURT"]:
            killer = 'world'
        else:
            killer = players[killer_num][0]
        victim = players[victim_num][0]
        return [killer_num, killer, victim, cause]

    elif event == "Hit":
        victim_num, attacker_num, zone, weapon, message = args.split(" ", 4)
        victim_num = int(victim_num)
        attacker_num = int(attacker_num)
        zone = int(zone)
        weapon = int(weapon)
        attacker = players[attacker_num][0]
        victim = players[victim_num][0]
        zone = hit_zone[zone]
        weapon = hit_item[weapon]
        return [attacker_num, attacker, victim, zone, weapon]

    elif event == "say":
        player_num, player_name, message = args.split(" ", 2)
        return [player_num, player_name, message]

    elif event == "InitGame":
        args = args.lstrip(" ").split("\\")
        args = [args[i:i + 2] for i in range(1, len(args), 2)]
        var_names = ("mapname", "g_gametype", "fraglimit", "timelimit")
        cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
        #print("cvars {}".format(cvars))
        return [cvars[v] for v in var_names]

    elif event == "ShutdownGame":
        return None

    elif event in ("ClientConnect", "ClientDisconnect", "ClientBegin", "ClientSpawn"):
        player_num = int(args)
        return player_num

    elif event == "ClientUserinfo":
        if "challenge" in args:
            num = int(args.split()[0])
            args = args.split("\\")
            args = [args[i:i + 2] for i in range(1, len(args), 2)]
            var_names = ("ip", "name")
            cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
            #print("cvars {}".format(cvars))
            return [num] + [cvars[v] for v in var_names]

    elif event == "ClientUserinfoChanged":
        num = args.split()
        name = args.split("\\")[1]
        return [num, name]
        
def execute_command(game_time, event, args):
    global stats, first_kill, first_nade, first_knife

    # players[x] = (name, score, address, ping)
    # stats[x] = [headshots, nade_kills, knife_kills]
    if event == "Kill":
        killer_num, killer, victim, cause = args
        if not first_kill and killer != victim:
            rcon("bigtext \"^4First kill: ^3{}\"".format(killer))
            first_kill = killer
            time.sleep(1)
        elif cause in ["UT_MOD_HEGRENADE", "UT_MOD_HK69"] and killer != victim:
            if not first_nade:
                rcon("bigtext \"^4First nade kill: ^3{}\"".format(killer))
                first_nade = killer
                time.sleep(1)
            add_score("nade", killer_num)
        elif cause in ["UT_MOD_KNIFE", "UT_MOD_KNIFE_THROWN"] :
            if not first_knife:
                rcon("bigtext \"^4First knife kill: ^3{}\"".format(killer))
                first_knife = killer
                time.sleep(1)
            add_score("knife", killer_num)
        print("{} killed {} with {}".format(killer, victim, cause))

    elif event == "Hit":
        attacker_num, attacker, victim, zone, weapon = args
        print("{} hit {} in {} with {}".format(attacker, victim, zone, weapon))
        if zone in ["HEAD", "HELMET"]:
            add_score("headshot", attacker_num)

    elif event == "say":
        player_num, player_name, message = args
        print("{} says: {}".format(player_name, message))

    elif event == "ShutdownGame":
        reset_stats()
        print("Changing map...")
        time.sleep(5)

    elif event == "InitGame":
        map_name, game_type, frag_limit, time_limit = args
        print("Map name: {} Gametype {}, {} kills, {} minutes".format(map_name, game_type, frag_limit, time_limit))

    elif event == "ClientConnect":
        num = args
        headshots, nade_kills, knife_kills = 0, 0, 0
        stats[int(num)] = [headshots, nade_kills, knife_kills]

    elif event == "ClientDisconnect":
        num = args
        print("Player {} is disconnecting".format(players[num][0]))
        remove_player(num)
        #print_player_info()

    elif event == "ClientBegin":
        num = args
        update_player_info()
        print_player_info()
        name = players[num][0]
        ip = players[num][2]
        country = ip_db.country_name_by_addr(ip)
        print("Player {} - {} connected from {}".format(num, name, country))
        # does everyone really need to know this
        #rcon("say {} connected from {}".format(name, country))

    elif event == "ClientUserinfo":
        if args:
            num, ip, name = args
            ip = ip.split(":")[0]

    elif event == "ClientUserinfoChanged":
        num, name = args
        update_player_info()
        #print_player_info()

####

def update_player_info():
    global players, stats 
    _, _, _, _, *player_info  = [s.decode("UTF-8") for s in rcon("status").split(b"\n")]

    for p in player_info:
        num, score, ping, rest = p.split(None, 3)
        # Parse nicknames with spaces
        name, lastmsg, address, qport, rate = rest.rsplit(None, 4)
        # Remove color codes
        name = re.sub(r"\^\d", "", name)
        # Drop port
        address = address.split(":")[0]
        players[int(num)] = (name, score, address, ping)
        stats[int(num)] = [0, 0, 0]

def print_player_info():
    print("Players: {}".format(players))
    for num, info in players.items():
        name, score, address, ping = info
        print("#{} - {}, {} points [{} - {}ms]".format(num, name, score, address, ping))

def remove_player(num):
    global players
    del players[int(num)]
    del stats[int(num)]

####

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.connect((ADDRESS, PORT))
server.settimeout(2)
update_player_info()
print_player_info()
reset_stats()

log = open("/home/urt/urt42/q3ut4/games.log", "r")
print("Listening...")

for line in live_tail(log):
    # Parsing
    game_time, event, raw_args = parse_event(line)
    #print("[{} ~ {} ~ {}]".format(game_time, event, raw_args))
    args = parse_args(event, raw_args)
    execute_command(game_time, event, args)
