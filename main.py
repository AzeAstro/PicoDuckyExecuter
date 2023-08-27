from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
from board import *
import digitalio
import socketpool
import usb_hid
import gc
import wifi
import time
import json
from struct import pack,unpack

# Keys for DuckyScript
# We will need it.
duckyCommands = {
    'WINDOWS': Keycode.WINDOWS,'WIN': Keycode.WINDOWS, 'GUI': Keycode.GUI,
    'APP': Keycode.APPLICATION, 'MENU': Keycode.APPLICATION, 'SHIFT': Keycode.SHIFT,
    'ALT': Keycode.ALT, 'CONTROL': Keycode.CONTROL, 'CTRL': Keycode.CONTROL,
    'DOWNARROW': Keycode.DOWN_ARROW, 'DOWN': Keycode.DOWN_ARROW, 'LEFTARROW': Keycode.LEFT_ARROW,
    'LEFT': Keycode.LEFT_ARROW, 'RIGHTARROW': Keycode.RIGHT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UPARROW': Keycode.UP_ARROW, 'UP': Keycode.UP_ARROW, 'BREAK': Keycode.PAUSE,
    'PAUSE': Keycode.PAUSE, 'CAPSLOCK': Keycode.CAPS_LOCK, 'DELETE': Keycode.DELETE,
    'END': Keycode.END, 'ESC': Keycode.ESCAPE, 'ESCAPE': Keycode.ESCAPE, 'HOME': Keycode.HOME,
    'INSERT': Keycode.INSERT, 'NUMLOCK': Keycode.KEYPAD_NUMLOCK, 'PAGEUP': Keycode.PAGE_UP,
    'PAGEDOWN': Keycode.PAGE_DOWN, 'PRINTSCREEN': Keycode.PRINT_SCREEN, 'ENTER': Keycode.ENTER,
    'SCROLLLOCK': Keycode.SCROLL_LOCK, 'SPACE': Keycode.SPACE, 'TAB': Keycode.TAB,
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D, 'E': Keycode.E,
    'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H, 'I': Keycode.I, 'J': Keycode.J,
    'K': Keycode.K, 'L': Keycode.L, 'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O,
    'P': Keycode.P, 'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X, 'Y': Keycode.Y,
    'Z': Keycode.Z, 'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3,
    'F4': Keycode.F4, 'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7,
    'F8': Keycode.F8, 'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11,
    'F12': Keycode.F12,
}




# Defining led for wireless connectivity status
led = digitalio.DigitalInOut(LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False

# Keyboard initialization
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayout(kbd)

# Mouse initialization
m = Mouse(usb_hid.devices)

# Some sleep before hard work ;)
time.sleep(.5)

# Setting global variables such as defaultDelay and previousLine(The last line that got executed)
defaultDelay=0
previousLine = ""

# These are global variables for mouse.
# mouseHold represents mouse button that is currently hold
mouseHold=[]
validMouseButtonStringList=["RIGHT_BUTTON","LEFT_BUTTON","MIDDLE_BUTTON"]


# This function parses configuration from config.json file.
# config.json must contain these 3 things: mode, ssid, password.
# Mode can be either "ap" or "station" (station means it is gonna connect to some wifi. ap means, it starts an access point or simply said, a wifi so you can connect the network.)
def parseConfig(configFile:str):
    try:
        with open(configFile,"r") as f:
            config=json.load(f)
        
        try:
            # Calls functions according to mode in config
            if config['mode']=="station" or config['mode']=="client":
                connectWifi(config['ssid'],config['password'])
            
            elif config['mode']=="ap":
                startWifi(config['ssid'],config['password'])
            
            # Fallback in case mode is mode is invalid
            else:
                startWifi("PicoDuckyExecuter","IMightBePoorButIAmSmart")
        # In case, you forgot to add ssid and password. Or you just want it to be as quick as possible.
        # Remember the SSID and Password. They will need you in order to connect Pico.
        except KeyError:
            startWifi("PicoDuckyExecuter","IMightBePoorButIAmSmart")
    except:
        # This applies only when you forgot to write config.json.
        # When config.json is not present or can't be read for some reason, it will start in AP mode and with this SSID and password.
        startWifi("PicoDuckyExecuter","IMightBePoorButIAmSmart")


# Creation of socketPool object for working with sockets
pool=socketpool.SocketPool(wifi.radio)

# This function creates access point so you can connect it and then run the script.
# Default IP address of Pico is 192.168.4.1 but you can change it.
# Check https://docs.circuitpython.org/en/latest/shared-bindings/wifi/index.html#wifi.Radio.set_ipv4_address_ap
def startWifi(ssid:str,password:str):
    wifi.radio.stop_station()
    wifi.radio.start_ap(ssid,password)
    #Turn on led when wifi is active
    led.value=True

# This function connects to wifi.
# Just read the function name. It does what it says.
def connectWifi(ssid:str,password:str):
    # Here, we try to connect network. It is in endless loop, so, it won't stop unless it connects to wifi
    # wifi.radio.ipv4_address is out IPv4 address. If we have this address, it means, we connected to wifi. So, this can be used as checking if we connected to wifi or not.
    while not wifi.radio.ipv4_address:
        try:
            wifi.radio.connect(ssid,password)
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
        time.sleep(10)
    # Turns led on when got connected to wifi
    led.value=True
# KEYBOARD FUNCTIONS
# Functions below are related to keyboard functionality.


# convertLine command for converting buttons such as ALT, F4, ENTER and etc and adding it into button list
def convertLine(line):
    newline = []
    for key in filter(None, line.split(" ")):
        key = key.upper()
        command_keycode = duckyCommands.get(key, None)
        if command_keycode is not None:
            newline.append(command_keycode)
        elif hasattr(Keycode, key):
            newline.append(getattr(Keycode, key))
        else:
            print(f"Unknown key: <{key}>")
    return newline

# Run buttons in list that got returned by convertLine function
def runScriptLine(line):
    for k in line:
        kbd.press(k)
    kbd.release_all()

# Typing string that has been given as argument
def sendString(line):
    layout.write(line)




## MOUSE FUNCTIONS
# Functions below are related to mouse functionality.

# This function is for handling mouse commands.
# Yes, I know, there are many if statements but beleive me, when you read code properly, it is ez.
def mouseHandler(line):
    global mouseHold
    # MOUSE_HOLD
    # Holds given mouse button.
    # It can hold couple mouse buttons at the same time. So, it is normal to write "MOUSE_HOLD LEFT_BUTTON" and "MOUSE_HOLD RIGHT_BUTTON" right in next line.
    if line.startswith("MOUSE_HOLD"):
        # Here we strip the given line, so we can get the button that is requested by DuckyScript.
        line=line.replace("MOUSE_HOLD","",1)
        line=line.strip()
        
        # Checks if given button is left button and that button is not already held.
        if line == "LEFT_BUTTON" and line not in mouseHold:
            m.press(Mouse.LEFT_BUTTON)
            mouseHold.append(line)
            
        elif line == "RIGHT_BUTTON" and line not in mouseHold:
            m.press(Mouse.RIGHT_BUTTON)
            mouseHold.append(line)
            
        elif line == "MIDDLE_BUTTON" and line not in mouseHold:
            m.press(Mouse.MIDDLE_BUTTON)
            mouseHold.append(line)
            
        # Runs in case of button is a valid mouse button but it is already held.
        elif line in validMouseButtonStringList and line in mouseHold:
            print("Button is already held.")
        
        # Runs if the given button is not valid button. For example, "MOUSE_HOLD DOORBELL_BUTTON" (I know it is a shitty example, but couldn't find anything better currently.)
        elif line not in validMouseButtonStringList:
            print("Unknown button")
    
    #MOUSE_MOVE
    # Moves mouse horizontally and vertically.
    # The first argument is horizontal and the second one is vertical movement.
    # For horizontal, positive number means up, negative means down.
    # For vertical, positive number means right, negative means left.
    # Remember: IT DOESN'T MOVE MOUSE TO CORDINATES, IT MOVES MOUSE LEFT/RIGHT AND UP/DOWN AND DOESN'T DEPEND ON SCREEN ITSELF.
    elif line.startswith("MOUSE_MOVE"):
        # validCordinates if a bool for confirming if given arguments are valid.
        validCordinates=None
        
        # Here we strip line as always for getting to arguments.
        line=line.replace("MOUSE_MOVE","",1)
        line=line.strip()
        
        # Here we try to convert give string cordinates into integer.
        # if fails, movement won't happen.
        try:
            line=line.split(" ")
            mouseHorizontal=int(line[0])
            mouseVertical=int(line[1])
            validCordinates=True
        except ValueError:
            print("Move accepts integer only")
            validCordinates=False
        
        # Here, checks if cordinates are valid. If valid, moves mouse according to them.
        if validCordinates:
            # Here, I switch mouseHorizontal value.
            # By deafult in mouse library of CircuitPython, negative means up, positive means down.
            # So, I did it for avoiding misunderstandings.
            if mouseHorizontal < 0:
                mouseHorizontal=abs(mouseHorizontal)
            else:
                mouseHorizontal=-abs(mouseHorizontal)
            
            m.move(mouseVertical,mouseHorizontal,0)
            
    #MOUSE_WHEEL
    # Moves mouse wheel up and down.
    # As in MOUSE_MOVE, positive up, negative down.
    # Scroll amount doesn't depend on screen or the object that is getting scrolled.
    elif line.startswith("MOUSE_WHEEL"):
        # As in MOUSE_MOVE, it is a bool that represents if given value for scrolling mouse is valid or not.
        validScrollAmount=None
        # Stripping(or "cutting". Don't you even dare to go to strip bar with a string.) line as always
        line=line.replace("MOUSE_WHEEL","",1)
        line=line.strip()
        # Here, we try to convert scroll amount that is given as string to the int so we can pass it as argument.
        try:
            scrollAmount=int(line)
            validScrollAmount=True
        except ValueError:
            validScrollAmount=False
            
            
        if validScrollAmount:
            m.move(0,0,scrollAmount)
    
    #MOUSE_RELEASE
    # This command releases the held button.
    # If button is not held, then it prints "Button is not held."
    elif line.startswith("MOUSE_RELEASE "):
        # Strip line parts as always...
        line=line.replace("MOUSE_RELEASE","",1)
        line=line.strip()
        # Checks if button that is given as argument is a valid mouse button.
        # If not, then prints "Unknown mouse button."
        if line in validMouseButtonStringList:
            # Check which button it was.
            # release() function releases that button.
            if line in mouseHold:
                if line == "RIGHT_BUTTON":
                    m.release(Mouse.RIGHT_BUTTON)
                    mouseHold.remove("RIGHT_BUTTON")
                elif line == "LEFT_BUTTON":
                    m.release(Mouse.LEFT_BUTTON)
                    mouseHold.remove("LEFT_BUTTON")
                elif line == "MIDDLE_BUTTON":
                    m.release(Mouse.MIDDLE_BUTTON)
                    mouseHold.remove("MIDDLE_BUTTON")
            # As I said earlier, if button is not held, then it prints that.
            else:
                print("Button is not held.")
        # Runs in case if given button is an invalid mouse button.
        # For example, "MOUSE_RELEASE BELLY_BUTTON" (As I said earlier, I am professional at shitty examples, but you got the point.)
        else:
            print("Unknown mouse button.")
            
            
    #MOUSE_CLICK
    # Click to mouse button.
    # Buttons are: LEFT_BUTTON, RIGHT_BUTTON, MIDDLE_BUTTON
    # You can make double clicks by stacking too MOUSE_CLICK.
    # For example:
    # MOUSE_CLICK LEFT_BUTTON
    # MOUSE_CLICK LEFT_BUTTON
    elif line.startswith("MOUSE_CLICK"):
        # Strip line again...
        line=line.replace("MOUSE_CLICK","",1)
        line=line.strip()
        # Checks if button that is given as argument is a valid mouse button.
        # If not, then prints "Unknown mouse button."
        if line in validMouseButtonStringList:
            if line == "RIGHT_BUTTON":
                m.click(Mouse.RIGHT_BUTTON)
            elif line == "LEFT_BUTTON":
                m.click(Mouse.LEFT_BUTTON)
            elif line == "MIDDLE_BUTTON":
                m.click(Mouse.MIDDLE_BUTTON)
        else:
            print("Unknown mouse button.")
    
    
    
    # Releases all mouse buttons.
    # I don't think we need that much of comments here.
    elif line.startswith("MOUSE_RELEASE_ALL"):
        m.release_all()
    
    # Runs in case, if invalid mouse command is given.
    # For example, "MOUSE_FLIP" (You got the point, didn't you?)
    else:
        print("Unknown mouse command.")




# This function is kinda handler. Handles the given line and calls functions according to given DuckyScript line
def parseLine(line):
    global defaultDelay
    if(line[0:3] == "REM"):
        pass
    elif(line[0:5] == "DELAY"):
        time.sleep(float(line[6:])/1000)
    elif(line[0:6] == "STRING"):
        sendString(line[7:])
    elif(line[0:13] == "DEFAULT_DELAY"):
        defaultDelay = int(line[14:]) * 10
    elif(line[0:12] == "DEFAULTDELAY"):
        defaultDelay = int(line[13:]) * 10
    elif(line[0:5] == "MOUSE"):
        mouseHandler(line)
    else:
        newScriptLine = convertLine(line)
        runScriptLine(newScriptLine)


# This function can be called as handler too but this function handles the whole payload.
def runPayload(duckyScript):
    global previousLine
    for line in duckyScript.splitlines():
        line = line.rstrip()
        if(line[0:6] == "REPEAT"):
            i=1
            for i in range(int(line[7:])):
                parseLine(previousLine)
                time.sleep(float(defaultDelay)/1000)
        else:
            parseLine(line)
            previousLine = line
        time.sleep(float(defaultDelay)/1000)





# Here the magic begins...
def main():
    
    #Here,we parse config and either create AP or connect to AP
    parseConfig("config.json")
    
    # Creation of socket object for connection between client and Pico
    mySoc=pool.socket(pool.AF_INET,pool.SOCK_STREAM)
    
    # I chose port 9999 but you can modify it as you want.
    mySoc.bind(("0.0.0.0",9999))
    
    #Yep, listening to one client at time is prefered. Reason is scripts that comes from couple clients sometimes can get mixed.
    # You don't want to someone else remove your shell backdoor script and type "start https://www.youtube.com/watch?v=dQw4w9WgXcQ" and then press enter, do you? ;))
    mySoc.listen(1)

    # It is in while True loop because, we don't want to Pico shut down when someone disconnects.
    # Pico will stop only when "!exit" command is received. And it will happen by raising error.
    while True:
        print("Waiting for connection...")
        with mySoc.accept()[0] as connSoc:
            print("Got connection.")
            
            # Here, payload receiving starts...
            while True:
                # Since, we don't want to limit payload length to some number, we want to receive its length before we receive the payload itself.
                # Which means, we can send payload as huge has memory can handle. Not that 1024 or 2048 length ones.
                # I used long int to send payload length. Long's limit is huge enough for one payload.
                payloadLength=bytearray(4)
                connSoc.recv_into(payloadLength,4)
                payloadLength=unpack("l",payloadLength)[0]
                
                #Here, payload is getting received. 
                payloadData=b""
                # Generic while True: socket.recv() loop but here, in CircuitPython, we got recv_into, not recv.
                while True:
                    if len(payloadData)>=payloadLength:
                        break
                    else:
                        # If payload length is over 2048, we receive it as chunks.
                        chunk=bytearray(2048)
                        connSoc.recv_into(chunk,2048)
                        payloadData+=chunk
                        # Now, you might wonder why we use replace.
                        # For the reason that I have no idea, when we sometimes receive payload, it gave some array of "\x00" in chunk.
                        # Even when payload didn't containt it or it wasn't sent by client.
                        # And before you say "Maybe last chunk contained it?", no it happened in full chunks as well. For example, payload length is 10K and it still had that null byte array at chunks that is in middle.
                        payloadData=payloadData.replace(b"\x00",b"")
                
                #Here, we convert received payload into string.
                payloadData=payloadData.decode()
                # It is a mini handler too.
                # Handles if the command that it sent by client is disconnect/exit request or a DuckyScript payload
                if payloadData=="!disconnect":
                    # As I said earlier, it disconnects one client and waits for other one to connect.
                    connSoc.close()
                    break
                elif payloadData=="!stop":
                    # Closing connection with client
                    connSoc.close()
                    # Stops the wireless connection
                    # wifi.radio.ap_active returns true if it is in AP mode.
                    if wifi.radio.ap_active:
                        wifi.radio.stop_ap()
                    # And here, if we get false from AP mode, then it is in station mode(or connected to another wifi)
                    # So, we disconnect it :D
                    else:
                        wifi.radio.stop_station()
                    #Turning off led
                    led.value=False
                    return False
                else:
                    # And here the payload is passed as argument into handler.
                    runPayload(payloadData)
                
                # GC is short for Garbage Collector. Here I use it clearing memory. It is really useful. Don't recommend to remove this line.
                gc.collect()
                
                    
if __name__=="__main__":
    # I made it this way so if you just need one function from this script, you can use it without running the code itself.
    main()

# Now, if you read the whole comments written here, then now you know the magic of "Willy Wonka's chocholate factory" ;)
# If you liked it, don't forget one fact: You can buy me one chocholate too ;)
# Good luck with your script! 







