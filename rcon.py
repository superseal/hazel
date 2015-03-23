import socket
import time
import re

from game_vars import hit_zone, hit_item, death_cause

(ADDRESS, PORT) = ("192.155.94.108", 27960)
password = "testserver"

players = {}
stats = {}

def live_tail(log):
    log.seek(0, 2)
    while 1:
        line = log.readline()
        if not line:
            time.sleep(0.2)
            continue
        yield line

def raw_command(cmd):
    time.sleep(0.5)
    message = b"\xff\xff\xff\xff" + ("%s\n" % cmd).encode("UTF-8")
    server.send(message)
    return server.recv(8096).replace(b"\xff\xff\xff\xff", b"").rstrip(b"\n")

def rcon(cmd):
    return raw_command("rcon {} {}".format(password, cmd))

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

    if event == "Kill":
        killer, victim, cause, message = args.split(" ", 3)
        cause = death_cause[int(cause)]
        if '<world>' in message or cause == "MOD_FALLING":
            killer = 'world'
        else:
            killer = players[int(killer)][0]
        victim = players[int(victim)][0]
        return [killer, victim, cause]
    elif event == "Hit":
        victim, attacker, zone, weapon, message = args.split(" ", 4)
        attacker = players[int(attacker)][0]
        victim = players[int(victim)][0]
        zone = hit_zone[int(zone)]
        weapon = hit_item[int(weapon)]
        return [attacker, victim, zone, weapon]
    elif event == "say":
        player_num, player_name, message = args.split(" ", 2)
        return [player_num, player_name, message]
    elif event == "InitGame":
        args = args.lstrip(" ").split("\\")
        args = [args[i:i + 2] for i in range(1, len(args), 2)]
        var_names = ("mapname", "g_gametype", "fraglimit", "timelimit")
        cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
        print("cvars {}".format(cvars))
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
            var_names = ("ip", "name", "gear")
            cvars = {cvar: cvalue for (cvar, cvalue) in args if cvar in var_names}
            print("cvars {}".format(cvars))
            return [num] + [cvars[v] for v in var_names]
    elif event == "ClientUserinfoChanged":
        num = args.split()
        name = args.split("\\")[1]
        return [num, name]
        
def execute_command(event, args):
    if event == "Kill":
        killer, victim, cause = args
        print("{} killed {} with {}".format(killer, victim, cause))
    elif event == "Hit":
        attacker, victim, zone, weapon = args
        print("{} hit {} in {} with {}".format(attacker, victim, zone, weapon))
    elif event == "say":
        player_num, player_name, message = args
        print("{} says: {}".format(player_name, message))
    elif event == "ShutdownGame":
        print("Changing map...")
        time.sleep(5)
    elif event == "InitGame":
        map_name, game_type, frag_limit, time_limit = args
        print("Map name: {} Gametype {}, {} kills, {} minutes".format(map_name, game_type, frag_limit, time_limit))
    elif event == "ClientDisconnect":
        num = args
        print("Player {} is disconnecting".format(players[num][0]))
        remove_player(num)
        print_player_info()
    elif event == "ClientBegin":
        update_player_info()
        print_player_info()
    elif event == "ClientUserinfo":
        if args:
            num, ip, name, gear = args
            print("Player {} - {} connected from {} - carrying {}".format(num, name, ip, gear))
    elif event == "ClientUserinfoChanged":
        num, name = args
        update_player_info()
        print_player_info()
        #print("Player {} is now {}".format(num, name))

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

def print_player_info():
    print("Players: {}".format(players))
    for num, info in players.items():
        name, score, address, ping = info
        print("#{} - {}, {} points [{} - {}ms]".format(num, name, score, address, ping))

def remove_player(num):
    global players
    del players[int(num)]

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.connect((ADDRESS, PORT))
server.settimeout(2)
update_player_info()
print_player_info()

log = open("/home/urt/urt42/q3ut4/games.log", "r")
print("Listening...")

for line in live_tail(log):
    # Parsing
    game_time, event, raw_args = parse_event(line)
    #print("[{} ~ {} ~ {}]".format(game_time, event, raw_args))
    args = parse_args(event, raw_args)
    execute_command(event, args)
