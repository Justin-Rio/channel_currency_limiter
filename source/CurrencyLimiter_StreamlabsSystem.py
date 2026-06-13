
# Created July 6, 2018
# Commissioned by Shiv(Discord) on behalf of lootchestDE(Twitch)

#---------------------------
#   Import Libraries
#---------------------------
import codecs
import json
import os
import sys
import time


sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import TimeStrings
from TimeStrings import *

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "Currency Limiter"
Website = "https://www.twitch.tv/indyofcomo"
Description = "Remove stream currency after viewer hits maximum viewing time per day."
Creator = "IndyOfComo"
Version = "0.9.0"

#---------------------------
#   Global Variables
#---------------------------
SettingsFile = os.path.join(os.path.dirname(__file__), "limiterSettings.json")
ScriptSettings = None
DailyFile = os.path.join(os.path.dirname(__file__), "REPLACE-ME-CurrencyLimits.json")
TodaysViewers = None
# Tick() could happen before Init(), and that would cause TodaysViewers==None
NextCheck = time.time() + 30



#---------------------------
#   [Required] Setting
#---------------------------
class Settings(object):
    def __init__(self, settingsFile=None):
        try:
           with codecs.open(settingsFile, encoding="utf-8-sig", mode="r") as f:
               self.__dict__ = json.load(f, encoding="utf-8")
               Parent.Log("CurLimitr", "Loaded settings file, {}".format(HHMM()))
        except Exception as e:
            Parent.Log("CurLimitr", "Didn't load settings file. {}".format(e))
            self.currency_tick = 6
            self.currency_payout = 1
            self.max_hours = 8
            global SettingsFile
            self.Save(SettingsFile)
        return

    def Reload(self, jsondata):
        self.__dict__ = json.loads(jsondata, encoding="utf-8")
        return

    def Save(self, settingsfile):
#         Parent.Log("CurLimitr", "$$$ Settings.Save(), {}".format(HHMM()))
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
            with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
                f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8')))
        except Exception as e:
           Parent.Log("CurLimitr", "Failed to save settings to file. {}".format(e))
        return


#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
    #   Load settings
    global SettingsFile, ScriptSettings
    ScriptSettings = Settings(SettingsFile)
    
    Load_Viewers()
    # Now that Init() has had a chance to Load_Viewers(), reset NextCheck so that
    #    the first Tick() is crediting people for time they actually watched.
    NextCheck = time.time() + ScriptSettings.currency_tick
    return


#---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
#---------------------------
def ReloadSettings(jsonData):
#     Parent.Log("CurLimitr", "$$$ ReloadSettings(), {}".format(HHMM()))
    ScriptSettings.__dict__ = json.loads(jsonData)
    ScriptSettings.Save(SettingsFile)
    return

#---------------------------
#   [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
#---------------------------
def Unload():
    Save_Viewers()
    return

#---------------------------
#   [Optional] ScriptToggled (Notifies you when a user disables your script or enables it)
#---------------------------
def ScriptToggled(state):
    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):
    return

#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#
# Topic: Remove_Extra_Currency()
#    Performing a batch job on such small increments is not the ideal solution. At the end of 
#    the day or stream would seem like a better approach for such a heavy task.
#    However, RemovePointsAll(dict<user, amnt>) will not remove points from offline users.
#    In addition, it is possible that someone spends their currency before currency has been
#    removed.
#---------------------------
def Tick():
    global NextCheck, TodaysViewers
    
    if time.time() >= NextCheck:
        if Parent.IsLive():
            if TodaysViewers == None:
#                 Parent.Log("CurLimitr", "---Tick() ==None")
                TodaysViewers = {"todays_date": DDMMYY()}
            elif TodaysViewers["todays_date"] == DDMMYY():
#                 Parent.Log("CurLimitr", "---Tick() ==DDMMYY")
                Update_Viewers()
                Remove_Extra_Currency()
            else:
#                 Parent.Log("CurLimitr", "---Tick() != DDMMYY")
                Save_Viewers()
                TodaysViewers.clear()
                TodaysViewers = {"todays_date": DDMMYY()}
            
            # Parent.SendStreamMessage("{}".format(Print_Viewers()))
        # Live or not... 
        NextCheck = time.time() + (ScriptSettings.currency_tick * 60)
    return


# ---------------------------------------------------------
#    [Optional]  Classes
# ---------------------------------------------------------
  
# ---------------------------------------------------------
#   [Optional] Methods
# ---------------------------------------------------------

def Update_Viewers():
    global TodaysViewers
    
    for viewr in Parent.GetViewerList():
        if TodaysViewers.has_key(viewr):
            TodaysViewers[viewr] = TodaysViewers[viewr] + ScriptSettings.currency_tick
        else:
            TodaysViewers[viewr] = ScriptSettings.currency_tick
    return


def Load_Viewers():
    global TodaysViewers
    #     Parent.Log("CurLimitr", "$$$ Load_Viewers(), {}".format(HHMM()))
    
    ddmmyy = DDMMYY()
    try:
        daily_file = DailyFile.replace("REPLACE-ME", ddmmyy, 1)
        if os.path.isfile(daily_file):
            try:
                with codecs.open(daily_file, encoding="utf-8-sig", mode="r") as f:
                    TodaysViewers = json.load(f, encoding="utf-8")
                    Parent.Log("CurLimitr", "{}: ln186 Loaded daily file {}".format(HHMM(), ddmmyy))
            except Exception as e1:     # failure to load
                Parent.Log("CurLimitr", "{}: ln188 Failed to load {} file. {}".format(HHMM(), ddmmyy, e1))
                os.rename(daily_file, daily_file.replace(ddmmyy, ddmmyy + "xFailedToLoad"))
                TodaysViewers = {"todays_date": ddmmyy}
        else:   # new day
            TodaysViewers = {"todays_date": ddmmyy}
    except Exception as e2:     # 
        Parent.Log("CurLimitr", "{}: ln194 Didn't load daily file {}. {}".format(HHMM(), ddmmyy, e2))
        TodaysViewers = {"todays_date": ddmmyy}
    return


def Save_Viewers():
    global TodaysViewers
#     Parent.Log("CurLimitr", "$$$ Save_Viewers(), {}".format(HHMM()))
    
    try:
        daily_file = DailyFile.replace("REPLACE-ME", DDMMYY(), 1)
        with codecs.open(daily_file, encoding="utf-8-sig", mode="w+") as f:
            json.dump(TodaysViewers, f, encoding="utf-8")
    except Exception as e:
        Parent.Log("CurLimitr", "Failed to save daily file. {}".format(e))
    return


def Remove_Extra_Currency():
    # Find those over maximum to take away currency
#     Parent.Log("CurLimitr", "$$$ Remove_Extra_Currency(), {}".format(HHMM()))
    max_minutes = ScriptSettings.max_hours * 60
    reductions = {}
    for d_viewr, li_val in TodaysViewers.iteritems():
        if d_viewr == "todays_date":
            pass
        elif li_val > max_minutes:
            reductions.update({d_viewr: ScriptSettings.currency_payout})
    # If there are any to take currency away from, process now using the Batch function
    if not len(reductions) == 0:
#         Parent.Log("CurLimitr", "$$$ Attempting to process batch removal, {}".format(HHMM()))
        dodgers = Parent.RemovePointsAll(reductions)
        if not len(dodgers) == 0:
            Parent.Log("CurLimitr", "{} {}: These users were not online to have their currency removed: {}".format(DDMMYY(), HHMM(), ", ".join(viewr for viewr in dodgers)))
    return


def Print_Viewers():
    global TodaysViewers
    temp = "; ".join("{}: {}".format(v_key, str(m_val)) for v_key, m_val in TodaysViewers.iteritems())
    return temp
