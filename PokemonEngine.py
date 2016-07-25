import subprocess
import time
import os
import shutil
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt

SAVEGAMELOC = "/home/ctralie/.vba/POKEMONRED981.sgm"
PYTHON3 = True
DISPLAY = ":0.0"
RECORD_TIME = 1

class Key(object):
    def __init__(self, key, actualkey, prob, image):
        self.key = key
        self.actualkey = actualkey
        self.prob = prob
        self.image = image

KEYS = {}
KEYS["Left"] = Key("Left", "Left", 0.166,  "PressingLeft.png")
KEYS["Right"] = Key("Right", "Right", 0.166, "PressingRight.png")
KEYS["Up"] = Key("Up", "Up", 0.166, "PressingUp.png")
KEYS["Down"] = Key("Down", "Down", 0.166, "PressingDown.png")
KEYS["A"] = Key("Z", "A", 0.166, "PressingA.png")
KEYS["B"] = Key("X", "B", 0.166, "PressingB.png")
KEYS["Start"] = Key("Return", "Start", 0.002, "PressingStart.png")
KEYS["Select"] = Key("BackSpace", "Select", 0.002, "PressingSelect.png")

def getRandomKey():
    num = np.random.rand()
    keys = [KEYS[k] for k in KEYS]
    idx = 0
    cumsum = keys[idx].prob
    while cumsum < num and idx < len(KEYS) - 1:
        idx += 1
        cumsum += keys[idx].prob
    return keys[idx].actualkey

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

def makeFrameLaTeX(filename, keyObj, text, wordRange):
    fin = open("template.tex")
    l = fin.readlines()
    s = "".join(l)
    fin.close()
    s = s.replace("SCREENSHOTGOESHERE", filename)
    s = s.replace("CONTROLLERGOESHERE", "ControllerImages/%s"%keyObj.image)
    before = text[0:wordRange[0]]
    during = text[wordRange[0]:wordRange[1]]
    after = text[wordRange[1]:]
    s = s.replace("TEXTGOESHERE", "%s\\textcolor{red}{%s}%s"%(before, during, after))
    fout = open("temp.tex", "w")
    fout.write(s)
    fout.close()
    subprocess.call(["pdflatex", "temp.tex"])
    #convert -density 150 input.pdf -quality 90 output.png
    subprocess.call(["convert", "-density", "150", "temp.pdf", "-quality", "90", filename])

def makeFrameHTML(filename, keyObj, text, wordRange):
    fin = open("template.html")
    l = fin.readlines()
    s = "".join(l)
    fin.close()
    s = s.replace("SCREENSHOTGOESHERE", filename)
    s = s.replace("CONTROLLERGOESHERE", "ControllerImages/%s"%keyObj.image)
    before = text[0:wordRange[0]]
    during = text[wordRange[0]:wordRange[1]]
    after = text[wordRange[1]:]
    s = s.replace("TEXTGOESHERE", "%s<font color = \"red\">%s</font>%s"%(before, during, after))
    fout = open("temp.html", "w")
    fout.write(s)
    fout.close()
    subprocess.call(["wkhtmltopdf", "temp.html", "temp.pdf"])
    #convert -density 150 input.pdf -quality 90 output.png
    subprocess.call(["convert", "-density", "150", "temp.pdf", "-quality", "90", filename])
    subprocess.call(["convert", filename, "-trim", "+repage", filename])

#Hits a key, records the video, and superimposes the gameboy
#controls and highlighted text in each frame
def hitKeyAndRecord(ID, keyObj, text, wordRange):
    filename = "temp.avi"
    if os.path.exists(filename):
        os.remove(filename)
    
    #Step 1: Load the saved game state and record the action
    recProc = startRecording(filename, ID, DISPLAY)
    time.sleep(0.2)
    hitKey(ID, keyObj.key, 300)
    time.sleep(RECORD_TIME)
    stopRecording(recProc)
    
    #Step 2: Output video frames to temporary directory
    subprocess.call(["avconv", "-i", filename, "-r", "30", "-f", "image2", "Temp/%d.png"])
    
    #Step 3: Superimpose the text and the gameboy control
    NFiles = len([f for f in os.listdir("Temp") if f[-3:] == 'png'])
    for i in range(1, NFiles+1):
        makeFrameHTML("Temp/%i.png"%i, keyObj, text, wordRange)
    return NFiles

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

if __name__ == '__main__2':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    hitKeyAndRecord(ID, KEYS["Left"], "RightTest.avi", "BEGINNING.sgm", "BEGINNING_RIGHT.sgm")

if __name__ == '__main__2':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    loadGame("BEGINNING.sgm", ID)

