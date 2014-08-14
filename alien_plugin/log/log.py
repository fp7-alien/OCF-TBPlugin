
def writeToLog(text):
    with open("/opt/ofelia/expedient/src/python/plugins/alien_plugin/log/logFile","a") as file:
        file.write(text)
        file.write("\n")