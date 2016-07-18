import subprocess
import time
import os
import shutil
import numpy as np

KEYS = ["Left", "Right", "Up", "Down", "Z", "X"]
SAVEGAMELOC = "/home/ctralie/.vba/POKEMONRED981.sgm"
PYTHON3 = True
DISPLAY = ":0.0"

def launchGame():
    #subprocess.Popen(["vba", "-4", "POKEMONRED98.GB"])
    subprocess.Popen(["vba", "POKEMONRED98.GB"])

#Get the window ID of the process
def getWindowID():    
    proc = subprocess.Popen(["xdotool", "search", "--name", "VisualBoy"], stdout=subprocess.PIPE)
    ID = 0
    while True:
        output=proc.stdout.readline()
        if (output == b'' or output == '') and proc.poll() is not None:
            break
        if output:
            ID = int(output.strip())
        rc = proc.poll()
    return ID

def getWindowGeometry(ID):
    proc = subprocess.Popen(["xdotool", "getwindowgeometry", "%i"%ID], stdout=subprocess.PIPE)
    res = []
    while True:
        output=proc.stdout.readline()
        if (output == b'' or output == '') and proc.poll() is not None:
            break
        if output:
            res.append(output.strip())
        rc = proc.poll()
    pos = res[1].split()[1]
    geom = res[2].split()[1]
    return (pos, geom)

#Move to the window and click on it to gain focus
def gainFocus(ID):    
    subprocess.call(["xdotool", "mousemove", "--window", "%i"%ID, "200", "200", "click", "1"])

def saveGame(filename, ID):
    subprocess.call(["xdotool", "keydown", "--window", "%i"%ID, "shift"])
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])
    subprocess.call(["xdotool", "keyup", "--window", "%i"%ID, "shift"])
    shutil.copyfile(SAVEGAMELOC, filename)

def loadGame(filename, ID):
    if os.path.exists(SAVEGAMELOC):
        os.remove(SAVEGAMELOC)
    shutil.copyfile(filename, SAVEGAMELOC)
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])

#Record window with ID to a file
def startRecording(filename, ID, display = ":1.0"):
    (pos, geom) = getWindowGeometry(ID)
    if PYTHON3:
        pos = str(pos)[2:-1]
    command = ["avconv", "-f", "x11grab", "-r", "30", "-s", geom, "-i", "%s+%s"%(display, pos), "-qscale", "0", filename]
    proc = subprocess.Popen(command)
    return proc

def stopRecording(proc):
    proc.terminate()

def hitKey(ID, key, delay = 500):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "key", "--window", "%i"%ID, "--delay", "%i"%delay, key]
    subprocess.call(command)

def holdKey(ID, key):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "keydown", "--window", "%i"%ID, key]
    print(command)
    subprocess.call(command)

def releaseKey(ID, key):
    #A delay (ms) is needed to make sure key taps register in the game
    command = ["xdotool", "keyup", "--window", "%i"%ID, key]
    print(command)
    subprocess.call(command)

if __name__ == '__main__2':
    display = ":1.0"
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    loadGame("BEGINNING.sgm", ID)

if __name__ == '__main__2':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    for i in range(3):
        hitKey(ID, 'z')
        time.sleep(0.1)
    saveGame("test.sgm", ID)

if __name__ == '__main__':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    recProc = startRecording("test.avi", ID, DISPLAY)
    time.sleep(1)
    loadGame("BEGINNING.sgm", ID)
    holdKey(ID, 'space')
    #time.sleep(3)
    for i in range(1000):
        key = KEYS[np.random.randint(len(KEYS))]
        hitKey(ID, key, 1000/30)
    releaseKey(ID, 'space')
    stopRecording(recProc)
    #saveGame("startScreen.sgm", ID)
