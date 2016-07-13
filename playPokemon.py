import subprocess
import time
import os
import shutil

SAVEGAMELOC = "/home/ctralie/.vba/POKEMONRED981.sgm"

def launchGame():
    subprocess.Popen(["vba", "-4", "POKEMONRED98.GB"])

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
def startRecording(filename, ID):
    (pos, geom) = getWindowGeometry(ID)
    command = ["avconv", "-f", "x11grab", "-r", "20", "-s", geom, "-i", ":0.0+%s"%str(pos)[2:-1], "-qscale", "0", filename]
    print(command)
    proc = subprocess.Popen(command)
    return proc

def stopRecording(proc):
    proc.terminate()

if __name__ == '__main__':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    recProc = startRecording("test.avi", ID)
    time.sleep(2)
    loadGame("BEGINNING.sgm", ID)
    time.sleep(2)
    stopRecording(recProc)
    #saveGame("startScreen.sgm", ID)
