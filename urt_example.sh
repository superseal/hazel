#!/bin/bash
##### The SCRIPT_PATH variable in config.py points to this file #####
##### Rename this file or edit the variable accordingly ##### 
##### Changing the example cvars provided here is okay #####
cd /home/user/Urban\ Terror
./Quake3-UrT-Ded.x86_64 +set fs_game +set dedicated 2 +set net_ip 192.168.1.100 +set net_port 27960 +set com_hunkmegs 128 +exec server.cfg
