import random
import time

import pygeoip

from config import GEOIP_PATH, LOW_GRAV_MAPS, LOW_GRAV
from .utils import log
from .comm import proc_write

ip_db = pygeoip.GeoIP(GEOIP_PATH)

def update_stat(death_cause, killer):
    if death_cause == "headshot":
        killer.headshots += 1
        if killer.headshots % 5 == 0:
            proc_write('say "^7{} has {} headshots"'.format(killer.name, killer.headshots))
        else:
            proc_write('tell "{}" "^7You have {} headshots"'.format(killer.name, killer.headshots))

    elif death_cause == "nade":
        killer.nade_kills += 1
        if killer.nade_kills % 5 == 0:
            proc_write('bigtext "^7{}: {} nade kills"'.format(killer.name, killer.nade_kills))
        else:
            proc_write('tell "{}" "^7You have {} nade kills"'.format(killer.name, killer.nade_kills))

    elif death_cause == "knife":
        killer.knife_kills += 1
        if killer.knife_kills % 5 == 0:
            proc_write('bigtext "^7{}: {} knife kills"'.format(killer.name, killer.knife_kills))
        else:
            proc_write('tell "{}" "^7You have {} knife kills"'.format(killer.name, killer.knife_kills))

def update_spree(killer, victim):
    if killer.name == victim.name or killer.name == "world":
        if killer.streak >= 5:
            proc_write('say "^1{} stopped their own killing spree ({} kills)"'.format(victim.name, victim.streak))
        killer.streak = 0
        return

    killer.streak += 1

    if (killer.streak % 5) == 0:
        proc_write('say "^2{} is on a killing spree ({} kills)"'.format(killer.name, killer.streak))
    if victim.streak >= 5:
        proc_write('say "^1{} stopped {}\'s killing spree ({} kills)"'.format(killer.name, victim.name, victim.streak))
    
    victim.streak = 0
    killer.longest_streak = max(killer.longest_streak, killer.streak)

def global_records(game):
    # Get players by max score
    players = game.players.values()

    streak_player = max(players, key=lambda p: p.longest_streak)
    knife_player = max(players, key=lambda p: p.knife_kills)
    nade_player = max(players, key=lambda p: p.nade_kills)
    headshot_player = max(players, key=lambda p: p.headshots)
   
    # Wish I knew a more elegant way of doing this
    record_string = "^7Records: "

    if streak_player.longest_streak:
        p = streak_player
        record_string += "^3{} ^4({}k streak)^7, ".format(p.name, p.longest_streak)
    else:
        record_string += "no streaks, "

    if knife_player.knife_kills:
        p = knife_player
        record_string += "^3{} ^4({} knives)^7, ".format(p.name, p.knife_kills)
    else:
        record_string += "no knives, "

    if nade_player.nade_kills:
        p = nade_player
        record_string += "^3{} ^4({} nades)^7, ".format(p.name, p.nade_kills)
    else:
        record_string += "no nades, "

    if headshot_player.headshots:
        p = headshot_player
        record_string += "^3{} ^4({} headshots)".format(p.name, p.headshots)
    else:
        record_string += "no headshots"

    proc_write('say "{}"'.format(record_string))

##### Actual commands #####
def execute_command(game, event, args):
    if event == "Hit":
        attacker_num, victim_num, zone, weapon = args
       
        attacker = game.players[attacker_num]
        victim = game.players[victim_num]

        #log("{} hit {} in {} with {}".format(attacker.name, victim.name, zone, weapon))
        if zone in ["HEAD", "HELMET"] and weapon != "UT_MOD_SPAS":
            update_stat("headshot", attacker)
            #log("{} has {} headshots".format(attacker.name, game.players[attacker_num].headshots))

    elif event == "Kill":
        killer_num, victim_num, cause = args

        killer = game.players[killer_num]
        victim = game.players[victim_num]

        update_spree(killer, victim)

        ## Suicides ##
        if killer.name == victim.name or killer.name == "world":
            return

        ## Normal deaths ##
        if not game.first_kill:
            proc_write('bigtext "^4First kill: ^3{}"'.format(killer.name))
            game.first_kill = killer

        # First kill could be a knife/nade kill
        if cause in ["UT_MOD_HEGRENADE", "UT_MOD_HK69"] and killer.name != victim.name:
            if not game.first_nade:
                proc_write('bigtext "^4First nade kill: ^3{}"'.format(killer.name))
                game.first_nade = killer
            update_stat("nade", killer)
            #log("{} has {} nade kills".format(killer.name, game.players[killer_num].nade_kills))
        elif cause in ["UT_MOD_KNIFE", "UT_MOD_KNIFE_THROWN"]:
            if not game.first_knife:
                proc_write('bigtext "^4First knife kill: ^3{}"'.format(killer.name))
                game.first_knife = killer
            update_stat("knife", killer)
            #log("* {} has {} knife kills".format(killer.name, game.players[killer_num].knife_kills))

        log("{} killed {} with {}".format(killer.name, victim.name, cause))
        proc_write('say "{} has a {} kill streak"'.format(killer.name, killer.streak))

    elif event == "say":
        num, message = args
        player = game.players[num]
        log("{} says: {}".format(player.name, message))

    elif event == "InitGame":
        map_name, game_type, frag_limit, time_limit = args

        # Low gravity maps
        if map_name in LOW_GRAV_MAPS:
            proc_write("set g_gravity {}".format(LOW_GRAV))

        # Gear restrictions
        prob = random.random()
        if 0 <= prob < 0.04:
            restrictions = "pistols"
            proc_write('set g_gear "HIJLMNZaceh"')
        elif 0.04 <= prob < 0.05:
            restrictions = "nades"
            proc_write('set g_gear "FGHIJKLMNZacefghRSTUVW"')
        elif 0.05 <= prob < 1:
            restrictions = ""
            proc_write('set g_gear ""')
        
        log("========== Map: {} ({}) ==========".format(map_name, restrictions))
        game.start(map_name, restrictions)
    
    elif event == "Exit":
        global_records(game)
        personal_records(game)
        game.reset_stats()

    elif event == "ClientConnect":
        num = args
        game.add_player(num, "-", "-")
    
    elif event == "ClientUserinfo":
        num, address, name = args
        name = name.strip()

        player = game.players[num]
        player.name = name.strip()
        player.address = address
        if not player.connected:
            player.connected = True

            record = ip_db.record_by_addr(address)
            if not record:
                log(">>> {} connected".format(name))
                return
            
            city = record['city']
            country = record['country_name']
            if city:
                log(">>> {} connected from {}, {}".format(name, city, country))
            else:
                log(">>> {} connected from {}".format(name, country))

    elif event == "ClientDisconnect":
        num = args
        player = game.players[num]
        log("<<< {} disconnected".format(player.name))
        game.remove_player(num)

    elif event == "ClientBegin":
        num = args
        player = game.players[num]
        if game.gear_restrictions == "pistols":
            proc_write("tell {} \"^3Gear restrictions for this match: ^4Pistols and grenades\"".format(player.name))
        elif game.gear_restrictions == "nades":
            proc_write("tell {} \"^3Gear restrictions for this match: ^4Grenades, HK69 and extra ammo\"".format(player.name))

    elif event == "ClientUserinfoChanged":
        num, name = args
