import subprocess
import time
import os
import shutil
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt
import scipy.misc

SAVEGAMELOC = "/home/ctralie/.vba/POKEMONRED981.sgm"
PYTHON3 = True
DISPLAY = ":0.0"
RECORD_TIME = 0.8
FRAMESPERSEC = 15

class Key(object):
    def __init__(self, key, actualkey, prob, image):
        self.key = key
        self.actualkey = actualkey
        self.prob = prob
        self.image = image

KEYS = {}
KEYS["Left"] = Key("Left", "Left", 0.186,  "PressingLeft.png")
KEYS["Right"] = Key("Right", "Right", 0.186, "PressingRight.png")
KEYS["Up"] = Key("Up", "Up", 0.186, "PressingUp.png")
KEYS["Down"] = Key("Down", "Down", 0.186, "PressingDown.png")
KEYS["A"] = Key("Z", "A", 0.202, "PressingA.png")
KEYS["B"] = Key("X", "B", 0.05, "PressingB.png")
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
    FNULL = open(os.devnull, 'w')
    subprocess.Popen(["vba", "POKEMONRED98.GB"], stdout = FNULL, stderr = FNULL)

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
    if os.path.exists(SAVEGAMELOC):
        os.remove(SAVEGAMELOC)
    subprocess.call(["xdotool", "keydown", "--window", "%i"%ID, "shift"])
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])
    subprocess.call(["xdotool", "keyup", "--window", "%i"%ID, "shift"])
    if not os.path.exists(SAVEGAMELOC):
        print("ERROR TYPE 1 saving game.  Retrying...")
        time.sleep(1)
        saveGame(filename, ID)
    elif os.stat(SAVEGAMELOC).st_size == 0:
        print("ERROR TYPE 2 saving game.  Retrying...")
        time.sleep(1)
        saveGame(filename, ID)
    else:
        shutil.copyfile(SAVEGAMELOC, filename)

def loadGame(filename, ID):
    if os.path.exists(SAVEGAMELOC):
        os.remove(SAVEGAMELOC)
    shutil.copyfile(filename, SAVEGAMELOC)
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F1"])

def closeGame(ID):
    subprocess.call(["xdotool", "keydown", "--window", "%i"%ID, "alt"])
    subprocess.call(["xdotool", "key", "--window", "%i"%ID, "F4"])
    subprocess.call(["xdotool", "keyup", "--window", "%i"%ID, "alt"])

#Record window with ID to a file
def startRecording(filename, ID, display = ":1.0"):
    (pos, geom) = getWindowGeometry(ID)
    if PYTHON3:
        pos = str(pos)[2:-1]
    command = ["ffmpeg", "-f", "x11grab", "-r", "30", "-s", geom, "-i", "%s+%s"%(display, pos), "-qscale", "0", filename]
    print(command)
    FNULL = open(os.devnull, 'w')
    proc = subprocess.Popen(command, stdout = FNULL, stderr = FNULL)
    return proc

def stopRecording(proc):
    proc.terminate()

def hitKey(ID, key, delay = 400):
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

#Return (image, [sx, ex, sy, ey] range for other frames)
def makeFrameTemplate(filename, keyObj, text, wordRange, pad = 10):
    #Load in and resize frame    
    frame = scipy.misc.imread(filename)
    W = 640
    frac = float(W)/frame.shape[1]
    frame = scipy.misc.imresize(frame, frac)
    
    #Load in and resize controls
    controls = scipy.misc.imread("ControllerImages/%s"%keyObj.image)
    H = frame.shape[0]
    frac = float(H)/controls.shape[0]
    controls = scipy.misc.imresize(controls, frac)
    
    #Figure out the width
    W = int(np.ceil(frame.shape[1] + controls.shape[1]))
    
    #Render text
    fin = open("textTemplate.html")
    l = fin.readlines()
    s = "".join(l)
    fin.close()
    s = s.replace("WIDTHGOESHERE", "%i"%W)
    textHTML = text
    before = textHTML[0:wordRange[0]]
    during = textHTML[wordRange[0]:wordRange[1]]
    after = textHTML[wordRange[1]:]
    s = s.replace("TEXTGOESHERE", "%s<font color = \"red\">%s</font>%s"%(before, during, after))
    fout = open("temp.html", "w")
    fout.write(s)
    fout.close()
    
    FNULL = open(os.devnull, 'w')
    subprocess.call(["wkhtmltopdf", "temp.html", "temp.pdf"], stdout = FNULL, stderr = FNULL)
    subprocess.call(["convert", "-density", "150", "temp.pdf", "-quality", "90", "temp.png"], stdout = FNULL, stderr = FNULL)
    subprocess.call(["convert", "temp.png", "-trim", "+repage", "temp.png"], stdout = FNULL, stderr = FNULL)
    #There's a small border around all sides that causes autocrop to fail the first
    #time
    text = scipy.misc.imread("temp.png")
    text = text[2:-2, 2:-2, :]
    scipy.misc.imsave("temp.png", text)
    subprocess.call(["convert", "temp.png", "-trim", "+repage", "temp.png"], stdout = FNULL, stderr = FNULL)
    
    #Load in text
    textImg = scipy.misc.imread("temp.png")
    frac = float(W)/textImg.shape[1]
    textImg = scipy.misc.imresize(textImg, frac)
    
    #Finally, set up image, and report range where gameboy frame resides
    H = textImg.shape[0] + controls.shape[0]
    I = 255*np.ones((H + 10*pad, W + 2*pad, 3))
    I[pad:pad+frame.shape[0], pad:pad+frame.shape[1], :] = frame[:, :, 0:3]
    I[pad:pad+controls.shape[0], pad+frame.shape[1]:pad+frame.shape[1]+controls.shape[1], :] = controls[:, :, 0:3]
    I[pad*3+frame.shape[0]:pad*3+frame.shape[0]+textImg.shape[0], pad:pad+textImg.shape[1], :] = textImg[:, :, 0:3]
    
    r = [pad, pad+frame.shape[0], pad, pad+frame.shape[1]]
    return (I, r)
    

#Hits a key, records the video, and superimposes the gameboy
#controls and highlighted text in each frame
def hitKeyAndRecord(ID, keyObj, filename):
    if os.path.exists(filename):
        os.remove(filename)
    
    #Step 1: Load the saved game state and record the action
    recProc = startRecording(filename, ID, DISPLAY)
    hitKey(ID, keyObj.key, 400)
    time.sleep(RECORD_TIME)
    stopRecording(recProc)

if __name__ == '__main__':
    launchGame()
    time.sleep(1)
    ID = getWindowID()
    recProc = startRecording("test.avi", ID, DISPLAY)
    time.sleep(1)
    loadGame("BEGINNING.sgm", ID)
    #holdKey(ID, 'space')
    #time.sleep(3)
    keysList = list(KEYS.keys())
    for i in range(10):
        key = KEYS[keysList[np.random.randint(len(KEYS))]]
        hitKey(ID, key.key, 1000/30)
    #releaseKey(ID, 'space')
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

