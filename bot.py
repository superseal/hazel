import socket
import time
import re

import pygeoip
from game_consts import HIT_ZONE, HIT_ITEM, DEATH_CAUSE, WORLD_NUM
from config import ADDRESS, PORT, PASSWORD, GEOIP_PATH, LOG_PATH


class Player():
    # Can't use a proper init function because the object needs to be created at ClientConnect
    def __init__(self):
        self.name = ""
        self.address = ""
        self.score = 0
        # ClientUserinfo always appears twice, use this to avoid double-printing
        self.connected = False
        # Stats
        self.longest_streak = 0
        self.headshots = 0
        self.knife_kills = 0
        self.nade_kills = 0

players = {}

# Global stats (not using a singleton just for this)
first_kill = ""
first_nade = ""
first_knife = ""

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
    return raw_command("rcon {} {}".format(PASSWORD, cmd))

####

def reset_stats():
    global first_kill, first_nade, first_knife
    first_kill = ""
    first_nade = ""
    first_knife = ""

    for num, p in players.items():
        p.headshots = 0
        p.knife_kills = 0
        p.nade_kills = 0
        p.longest_streak = 0

def inc_stat(kill_type, killer):
    if kill_type == "headshot":
        killer.headshots += 1
        kill_name = "headshots"
        points = killer.headshots
    elif kill_type == "nade":
        killer.nade_kills += 1
        kill_name = "nade kills"
        points = killer.nade_kills
    elif kill_type == "knife":
        killer.knife_kills += 1
        kill_name = "knife kills"
        points = killer.knife_kills
    
    if (points % 5) == 0:
        rcon("say \"^7{} has {} {}\"".format(killer.name, points, kill_name))
    else:
        rcon("tell \"{}\" \"^7You have {} {}\"".format(killer.name, points, kill_name))

def update_spree(killer, victim):
    killer.longest_streak += 1

    if (killer.longest_streak % 5) == 0:
        rcon("say \"^2{} is on a killing spree ({} kills)\"".format(killer.name, killer.longest_streak))

    if victim.longest_streak >= 5:
        rcon("say \"^1{} stopped {}'s killing spree ({} kills)\"".format(killer.name, victim.name, victim.longest_streak))
    
    victim.longest_streak = 0

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
    # ClientUserinfo contains an IP and a port, keep the colon
    # The colon is useless in other commands
    if event != "ClientUserinfo":
        args = args.replace(":", "")

    if event == "InitGame":
        # Partition arguments into tuples
        args = args.lstrip(" ").split("\\")
        args = [args[i:i + 2] for i in range(1, len(args), 2)]

        var_names = ("mapname", "g_gametype", "fraglimit", "timelimit")
        cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
        return [cvars[v] for v in var_names]

    elif event == "ShutdownGame":
        return None

    elif event in ("ClientConnect", "ClientDisconnect", "ClientBegin", "ClientSpawn"):
        player_num = int(args)
        return player_num

    elif event == "ClientUserinfo":
        num = int(args.split()[0])
        # Debug 
        raw_args = args
        # Partition arguments into tuples
        args = args.split("\\")
        args = [args[i:i + 2] for i in range(1, len(args), 2)]

        var_names = ("ip", "name")
        cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
        try:
            return [num] + [cvars[v] for v in var_names]
        except:
            print("Name failed, got {}".format(raw_args))
            print("Split args are {}".format(args))
            return [num, "address derp", players[num].name]

    elif event == "ClientUserinfoChanged":
        num = int(args.split()[0])
        name = args.split("\\")[1]
        return [num, name]
    
    elif event == "Kill":
        killer_num, victim_num, cause, message = args.split(" ", 3)
        killer_num, victim_num, cause = int(killer_num), int(victim_num), int(cause)
        
        cause = DEATH_CAUSE[cause]
        if '<world>' in message or cause in ["MOD_FALLING", "MOD_WATER", "MOD_LAVA", "MOD_TRIGGER_HURT"]:
            killer_num = WORLD_NUM

        return [killer_num, victim_num, cause]

    elif event == "Hit":
        victim_num, attacker_num, zone, weapon, message = args.split(" ", 4)
        victim_num, attacker_num, zone, weapon = int(victim_num), int(attacker_num), int(zone), int(weapon)
        
        zone = HIT_ZONE[zone]
        weapon = HIT_ITEM[weapon]
        return [attacker_num, victim_num, zone, weapon]

    elif event == "say":
        player_num, player_name, message = args.split(" ", 2)
        player_num = int(player_num)

        return [player_num, message]

def execute_command(game_time, event, args):
    global players, first_kill, first_nade, first_knife

    if event == "Hit":
        attacker_num, victim_num, zone, weapon = args
       
        attacker = players[attacker_num]
        victim = players[victim_num]

        #print("{} hit {} in {} with {}".format(attacker.name, victim.name, zone, weapon))
        if zone in ["HEAD", "HELMET"] and weapon != "UT_MOD_SPAS":
            inc_stat("headshot", attacker)
            #print("{} has {} headshots".format(attacker.name, players[attacker_num].headshots))

    elif event == "Kill":
        killer_num, victim_num, cause = args

        killer = players[killer_num]
        victim = players[victim_num]

        # Discard suicides
        if not first_kill and killer.name != victim.name and killer.name != "world":
            rcon("bigtext \"^4First kill: ^3{}\"".format(killer.name))
            first_kill = killer
            time.sleep(1)
        
        # First kill could be a knife/nade kill
        if cause in ["UT_MOD_HEGRENADE", "UT_MOD_HK69"] and killer.name != victim.name:
            if not first_nade:
                rcon("bigtext \"^4First nade kill: ^3{}\"".format(killer.name))
                first_nade = killer
                time.sleep(1)
            inc_stat("nade", killer)
            #print("{} has {} nade kills".format(killer.name, players[killer_num].nade_kills))
        elif cause in ["UT_MOD_KNIFE", "UT_MOD_KNIFE_THROWN"] :
            if not first_knife:
                rcon("bigtext \"^4First knife kill: ^3{}\"".format(killer.name))
                first_knife = killer
                time.sleep(1)
            inc_stat("knife", killer)
            #print("* {} has {} knife kills".format(killer.name, players[killer_num].knife_kills))

        update_spree(killer, victim)
        print("x {} killed {} with {}".format(killer.name, victim.name, cause))

    elif event == "say":
        num, message = args
        player = players[num]
        print("   {} says: {}".format(player.name, message))

    elif event == "InitGame":
        map_name, game_type, frag_limit, time_limit = args
        print("====== Map: {} ======".format(map_name))
    
    elif event == "ShutdownGame":
        reset_stats()
        time.sleep(5)

    elif event == "ClientConnect":
        num = args
        players[num] = Player()
    
    elif event == "ClientUserinfo":
        num, address, name = args
        player = players[num]
        if not player.connected:
            address = address.split(":")[0]
            country = ip_db.country_name_by_addr(address)
            # Remove color codes
            name = re.sub(r"\^\d", "", name)
            print(">>> {} connected from {}".format(name, country))
            player.connected = True

    elif event == "ClientDisconnect":
        num = args
        print("<<< {} disconnected".format(players[num].name))
        remove_player(num)

    elif event == "ClientBegin":
        num = args
        name, address, score = get_game_status()[num]
        players[num].name = name
        players[num].address = address
        players[num].score = score
        # does everyone really need to know this
        #rcon("say {} connected from {}".format(name, country))

    elif event == "ClientUserinfoChanged":
        num, name = args

####

def get_game_status():
    _, _, _, _, *player_info = [s.decode("UTF-8") for s in rcon("status").split(b"\n")]

    status = {}
    for p in player_info:
        num, score, ping, rest = p.split(None, 3)
        num = int(num)
        # Parse nicknames with spaces
        name, lastmsg, address, qport, rate = rest.rsplit(None, 4)
        # Remove color codes
        name = re.sub(r"\^\d", "", name)
        # Drop port
        address = address.split(":")[0]
        status[num] = (name, address, score)
    return status

def create_players(status):
    global players

    # Having a "world" player makes Hit and Kill logic simpler
    players[WORLD_NUM] = Player()
    players[WORLD_NUM].name = "world"
    players[WORLD_NUM].address = "0.0.0.0"

    for num, info in status.items():
        name, address, score = info
        players[num] = Player()
        # Don't blame me, read the comment in the Player class
        players[num].name = name
        players[num].address = address
        players[num].score = score

def print_player_info():
    for num, p in players.items():
        if num != WORLD_NUM:
            print("#{} - {}, {}, {} points".format(num, p.name, p.address, p.score))

def remove_player(num):
    global players
    del players[num]

####

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.connect((ADDRESS, PORT))
server.settimeout(60)

ip_db = pygeoip.GeoIP(GEOIP_PATH)

status = get_game_status()
create_players(status)
print_player_info()

log = open(LOG_PATH, "r")

for line in live_tail(log):
    # Parsing
    game_time, event, raw_args = parse_event(line)
    #print("[{} ~ {} ~ {}]".format(game_time, event, raw_args))
    args = parse_args(event, raw_args)
    execute_command(game_time, event, args)
