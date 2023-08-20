# ONLY FOR RASPBERRY PICO W

# PicoDuckyExecuter
Basic DuckyScript executer with  input support. Payload can be sent over network

Executes Duckyscript that is recieved over network.
Some parts implemented from [coder12341's pico-ducky](https://github.com/coder12341/pico-ducky) project.

## Script
For now, script support these Duckyscript keywords: REM, STRING, DELAY, REPEAT, MOUSE_HOLD, MOUSE_RELEASE, MOUSE_CLICK, MOUSE_WHEEL,MOUSE_MOVE, MOUSE_RELEASE_ALL  
I plan to add Consumer controls too such as VOLUME_INCREASE, NEXT_TRACK and etc.  
If you read this and consumer controls aren't added yet and 3 months passed from last commit, write me in Instagram or Discord or even in GitHub itself(if you know how.)

## Installation
1) Install CircuitPython to Raspberry Pico W
2) Install [`adafruit_hid`](https://pypi.org/project/adafruit-circuitpython-hid/) package to it
3) Drop main.py to root folder of pico
4) Have fun! ;)

## Usage
As if you read the code, you can see that you can directly connect it over sockets. So, I will show 2 methods to connect it.  

### 1) Python `sockets` library
Here, process is very simple: create a TCP socket object, connect to Pico's address and send payload using `send` function.  
Example:  
```py
import socket
import struct

duckyScript="""
REM This is test script
GUI R
DELAY 1000
STRING cmd
ENTER
DELAY 1000
STRING ipconfig
ENTER
DELAY 500
REM For MOUSE_WHEEL, positive number means, scroll up,negative means, scroll down
MOUSE_WHEEL 5
REM MOUSE_MOVE moves mouse. First value is horizontal cordinate, second is vertical.
REM For horizontal, positive value means up, negative down
REM For vertical, positive value means right, negative left
MOUSE_MOVE 100 -150
REM For MOUSE_HOLD, we can use mouse buttons to hold till MOUSE_RELEASE is given.
REM Available mouse buttons are: LEFT_BUTTON,RIGHT_BUTTON and MIDDLE_BUTTON
MOUSE_HOLD LEFT_BUTTON
MOUSE_MOVE -200 200
REM MOUSE_RELEASE is releases button that is held by MOUSE_HOLD
MOUSE_RELEASE LEFT_BUTTON
REM MOUSE_CLICK clicks mouse button. As I said earlier, you only can use available mouse buttons.
MOUSE_CLICK RIGHT_BUTTON
ENTER
REPEAT 7
MOUSE_CLICK RIGHT_BUTTON
"""

payload=struct.pack("l",len(duckyScript))+duckyScript.encode()
disconnectMessage=struct.pack("l",len("!disconnect"))+"!disconnect".encode()

picoSoc=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
picoSoc.connect(("192.168.1.3",9999)) # According to my code on `main.py` file, the TCP server runs on port 9999. You can change it how you want.


picoSoc.send(payload) # Send the payload
picoSoc.send("!disconnect".encode()) # Disconnect after sending payload.

# You can use `!exit` to completely stop the pico.
# It will raise error at pico and pico will completely stop.
# But sending payload needs to be similar to how we send disconnect message or payload.
# Length of payload should be packed as long and then payload should be attached to it.
```

### 2) [PicoPayloadSender](https://github.com/AzeAstro/PicoPayloadSender)
It is my custom sender. A GUI app written in PyQt6. Can be used in Windows, Linux, Mac and so on(as long as you can use python and PyQt6 library.)  

## Donations
If you really want to send donation contact me. (No matter how much. Anything that is 1 USD or higher is accepted.)  
Social media accounts:  
1) Instagram: [@atlas_c0](https://www.instagram.com/atlas_c0/)
2) Discord: @atlas_c0
