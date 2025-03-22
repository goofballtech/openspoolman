import os
from config import PRINTER_ID, EXTERNAL_SPOOL_AMS_ID, EXTERNAL_SPOOL_ID
from datetime import datetime
from zoneinfo import ZoneInfo
from print_history import update_filament_spool
import json

from spoolman_client import consumeSpool, patchExtraTags, fetchSpoolList

SPOOLS = {}

def trayUid(ams_id, tray_id):
  return f"{PRINTER_ID}_{ams_id}_{tray_id}"

def getAMSFromTray(n):
    return n // 4

def augmentTrayDataWithSpoolMan(spool_list, tray_data, tray_id):
  tray_data["matched"] = False
  for spool in spool_list:
    if spool.get("extra") and spool["extra"].get("active_tray") and spool["extra"]["active_tray"] == json.dumps(tray_id):
      #TODO: check for mismatch
      tray_data["name"] = spool["filament"]["name"]
      tray_data["vendor"] = spool["filament"]["vendor"]["name"]
      tray_data["remaining_weight"] = spool["remaining_weight"]
      
      if "last_used" in spool:
        try:
            dt = datetime.strptime(spool["last_used"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=ZoneInfo("UTC"))
        except ValueError:
            dt = datetime.strptime(spool["last_used"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=ZoneInfo("UTC"))

        local_time = dt.astimezone()
        tray_data["last_used"] = local_time.strftime("%d.%m.%Y %H:%M:%S")

      else:
          tray_data["last_used"] = "-"
          
      if "multi_color_hexes" in spool["filament"]:
        tray_data["tray_color"] = spool["filament"]["multi_color_hexes"]
        tray_data["tray_color_orientation"] = spool["filament"]["multi_color_direction"]
        
      tray_data["matched"] = True
      break

  if tray_data.get("tray_type") and tray_data["tray_type"] != "" and tray_data["matched"] == False:
    tray_data["issue"] = True
  else:
    tray_data["issue"] = False

def spendFilaments(printdata):
  if printdata["ams_mapping"]:
    ams_mapping = printdata["ams_mapping"]
  else:
    ams_mapping = EXTERNAL_SPOOL_AMS_ID

  """
  "ams_mapping": [
            1,
            0,
            -1,
            -1,
            -1,
            1,
            0
        ],
  """
  tray_id = EXTERNAL_SPOOL_ID
  ams_id = EXTERNAL_SPOOL_AMS_ID
  
  ams_usage = []
  for filamentId, filament in printdata["filaments"].items():
    if ams_mapping[0] != EXTERNAL_SPOOL_ID:
      tray_id = ams_mapping[filamentId - 1]   # get tray_id from ams_mapping for filament
      ams_id = getAMSFromTray(tray_id)        # caclulate ams_id from tray_id
      tray_id = tray_id - ams_id * 4          # correct tray_id for ams
    
    #if ams_usage.get(trayUid(ams_id, tray_id)):
    #    ams_usage[trayUid(ams_id, tray_id)]["usedGrams"] += float(filament["used_g"])
    #else:
      ams_usage.append({"trayUid": trayUid(ams_id, tray_id), "id": filamentId, "usedGrams":float(filament["used_g"])})

  for spool in fetchSpools():
    #TODO: What if there is a mismatch between AMS and SpoolMan?
                 
    if spool.get("extra") and spool.get("extra").get("active_tray"):
      #filament = ams_usage.get()
      active_tray = json.loads(spool.get("extra").get("active_tray"))

      # iterate over all ams_trays and set spool in print history, at the same time sum the usage for the tray and consume it from the spool
      used_grams = 0
      for ams_tray in ams_usage:
        if active_tray == ams_tray["trayUid"]:
          used_grams += ams_tray["usedGrams"]
          update_filament_spool(printdata["print_id"], ams_tray["id"], spool["id"])
        
      if used_grams != 0:
        consumeSpool(spool["id"], used_grams)
        

def setActiveTray(spool_id, spool_extra, ams_id, tray_id):
  if spool_extra == None:
    spool_extra = {}

  if not spool_extra.get("active_tray") or json.loads(spool_extra.get("active_tray")) != trayUid(ams_id, tray_id):
    patchExtraTags(spool_id, spool_extra, {
      "active_tray": json.dumps(trayUid(ams_id, tray_id)),
    })

    # Remove active tray from inactive spools
    for old_spool in fetchSpools(cached=True):
      if spool_id != old_spool["id"] and old_spool.get("extra") and old_spool["extra"].get("active_tray") and json.loads(old_spool["extra"]["active_tray"]) == trayUid(ams_id, tray_id):
        patchExtraTags(old_spool["id"], old_spool["extra"], {"active_tray": json.dumps("")})
  else:
    print("Skipping set active tray")

# Fetch spools from spoolman
def fetchSpools(cached=False):
  global SPOOLS
  if not cached or not SPOOLS:
    SPOOLS = fetchSpoolList()
    
    for spool in SPOOLS:
      if "multi_color_hexes" in spool["filament"]:
        spool["filament"]["multi_color_hexes"] = spool["filament"]["multi_color_hexes"].split(',')
        
  return SPOOLS