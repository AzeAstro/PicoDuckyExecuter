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
from struct import pack,unpack

# Keys for DuckyScript
# It will need us
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

# Creation of socketPool object for working with sockets
pool=socketpool.SocketPool(wifi.radio)


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
    else:
        newScriptLine = convertLine(line)
        runScriptLine(newScriptLine)


# This function can be called as handler too but this function handles the whole payload.
def runPayload(duckyScript):
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
    # Here, we try to connect network. It is in endless loop, so, it won't stop unless it connects to wifi
    while not wifi.radio.ipv4_address:
        try:
            wifi.radio.connect("someWifi","somePass")
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
        time.sleep(10)
    
    # Turns led on when got connected to wifi
    led.value=True

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
                    # Here, exit() function raises error. Since CircuitPython doesn't have exit function like regular python, it can be used here.
                    # Even if exit function existed, both variants(function and raised error) would do the same job for us.
                    connSoc.close()
                    exit()
                else:
                    # And here the payload is passed as argument into handler.
                    runPayload(payloadData)
                
                # GC is short for Garbage Collector. Here I use it clearing memory. It is really useful. Don't recommend to remove this line.
                gc.collect()
                
                    
if __name__=="__main__":
    # I made it this way so if you just need one function from this script, you can use it without running the code itself.
    main()

# Now, if you read the whole comments written here, then now you know the magic of "Willy Wonka's chocholate factory" ;))
# If you liked it, don't forget one fact: You can buy me one chocholate too ;)
# Good luck with your script! 





