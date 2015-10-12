#!/usr/bin/env python3
# coding: utf-8
import os
import time
import re
import random
import traceback
import sys
import collections

from ptyprocess import *

from lib.game_consts import WORLD_NUM
from lib.parser import parse_line
from lib.actions import execute_command
from lib.comm import proc_read, proc_write
from lib.utils import log
from config import LOW_GRAV, MAP_LIST

class Player():
    # Can't use a proper init function because the object needs to be created at ClientConnect
    # The auth system requires the server to send an extra ClientConnect/ClientUserinfo event
    # Naively creating the Player object on every ClientUserinfo event would execute commands twice
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.score = 0
        self.gear = ""
        # Avoid executing ClientUserinfo events twice
        self.connected = False
        # Stats
        self.streak = 0
        self.headshots = 0
        self.knife_kills = 0
        self.nade_kills = 0

        self.longest_streak = 0

    def __repr__(self):
        return "<name {} | address {} [{}]>".format(self.name, self.address, self.connected)

# Python forced me to use a singleton ;_;
class Game():
    def __init__(self):
        self.players = {}

        self.first_kill = ""
        self.first_nade = ""
        self.first_knife = ""
        self.gear_restrictions = ""
        
        # Having a "world" player makes Hit and Kill logic simpler
        self.add_player(WORLD_NUM, "world", "0.0.0.0")

        self.mapcycle = []
        # Keeps track of the current map so restarts don't alter the mapcycle
        self.current_map = ""
    
    def add_player(self, num, name, address):
        self.players[num] = Player(name, address)
    
    def remove_player(self, num):
        del self.players[num]
        
    def reset_stats(self):
        self.first_kill = ""
        self.first_nade = ""
        self.first_knife = ""

        for num, p in self.players.items():
            p.headshots = 0
            p.knife_kills = 0
            p.nade_kills = 0
            p.streak = 0
            p.longest_streak = 0

    def print_player_info(self):
        players = self.players
        if len(players) <= 1:
            print("   (no players)")
            return
        for num, p in players.items():
            if num != WORLD_NUM:
                print("#{} - {}, {}, {} points".format(num, p.name, p.address, p.score))

####
game = Game()
print("Loading...")
while 1:
    try:
        proc_event = proc_read()
        if not proc_event:
            continue
        event, args = parse_line(proc_event)
        #print("   event {!r} args {!r}".format(event, args))
        execute_command(game, event, args)
    except Exception as derp:
        for frame in traceback.extract_tb(sys.exc_info()[2]):
            fname, lineno, fn, text = frame
            print("Error in %s on line %d" % (fname, lineno))
        print(derp)

