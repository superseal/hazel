############################################
#### Rename to config.py before running ####
############################################

# Path to the bash script that runs the server binary
SCRIPT_PATH = ["/home/user/Urban Terror/urt.sh", "--long-arg"]

# Path to GeoLiteCity.dat
GEOIP_PATH = "/home/user/Documents/GeoLiteCity.dat"

# Low gravity settings
LOW_GRAV = 200

# D: default, C: custom
# t: tiny (2-5 players), n: normal (4-10 players), b: big (6-15 players), h: huge (10-20 players)
# L: low gravity
MAP_LIST = {
    # Default maps
    "ut4_prominence": "Dt-",
    "ut4_dressingroom": "Dt-",

    "ut4_swim": "Dn-",
    "ut4_uptown": "Dn-",
    "ut4_ricochet": "Dn-",
    "ut4_prague": "Dn-",
    "ut4_ambush": "Dn-",
    "ut4_kingpin": "Dn-",
    "ut4_tunis": "Dn-",
    "ut4_tombs": "Dn-",
    "ut4_crossing": "Dn-",
    "ut4_elgin": "Dn-",
    "ut4_raiders": "Dn-",
    "ut4_snoppis": "Dn-",
    "ut4_sanc": "Dn-",

    "ut4_toxic": "Db-",
    "ut4_subway": "Db-",
    "ut4_austria": "Db-",
    "ut4_bohemia": "Db-",
    "ut4_ramelle": "Db-",
    "ut4_suburbs": "Db-",
    "ut4_thingley": "Db-",
    "ut4_riyadh": "Db-",
    "ut4_ghosttown": "Db-",
    "ut4_docks": "Db-",
    "ut4_horror": "Db-",
    "ut4_eagle": "Dh-",
    
    # Custom maps
    "ut4_cemetery666": "Ct-",
    "ut4_quickfight2": "Ct-",

    "ut4_slumwar": "Cn-",
    "ut4_tactics2": "Cn-",
    "ut4_shipwreck": "Cn-",
    "ut4_derelict_b1": "Cn-",
    "ut4_alps": "Cn-",
    "ut4_orbital_sl": "Cn-",
    "ut4_australia_beta": "Cn-",
    "ut4_loadzone": "Cn-",
    "ut4_kaysersberg_a2": "Cn-",
    "ut4_blitzkrieg": "Cn-",
    "ut4_breathe_b2": "Cn-",
    "estatica": "Cn-",
    "chronic": "Cn-",
    "ut4_paris_v2": "Cn-",
    "ut4_terrorism3": "Cn-",
    "runtfest": "CnL", 
    "wop_diner": "CnL",
    "wop_cabin": "CnL",
    "wop_backyard": "CnL",

    "ut4_desolate_rc1": "Cb-",
    "ut4_dam_fixed": "Cb-",
    "ut4_formad_b4": "Cb-",
    "ut4_midnight": "Cb-",
    "ut4_heroic_beta1": "Cb-",
    "ut4_blitzkrieg2": "Cb-",
    "ut4_antic": "Cb-",
    "ut4_beijing_b3": "Cb-",
    "ut4_laneway4_beta": "Cb-",
    "ut4_sewerlair": "Cb-",
    "ut4_ripwinter_b2": "Cb-",
    "ut4_terrorism4": "Cb-",
    "ut4_terrorism5": "Cb-",
    "ut4_terrorism6": "Cb-",
    "ut4_terrorism7": "Cb-",
    "ut4_terrorism8": "Cb-",
    "ut4_shahideen": "Cb-",
    "ut4_cave_beta": "Cb-",
    "ut_lostbase": "Cb-",
    "wop_bath": "CbL", 
    "wop_padkitchen": "CbL",
    "wop_padlibrary": "CbL",
    "wop_padship": "CbL",
    "wop_padattic": "CbL",
    
    "ut4_edo_b1": "Ch-",
    "ut4_metro_v2": "Ch-",
    "ut4_sima_b2": "Ch-",
    "ut4_deception_v2": "Ch-",
}
