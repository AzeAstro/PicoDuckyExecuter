import json


settings={}
with open("config.json","r") as f:
    settings=json.load(f)

print(f"Mode: {settings['mode'].upper()}\nSSID: {settings['ssid']}\nPassword: {settings['password']}")
print("\nThese are current settings")

while True:
    mode=input("Enter the mode (AP/Station): ").lower()
    if mode in ["ap","station"]:
        break
    else:
        print("Invalid mode. Write either AP or Station")

ssid=input("Enter the SSID: ")

while True:
    passwd=input("Enter the password (length should be 8-63): ")
    if len(passwd)< 8:
        print("Password is too short.")
    elif len(passwd) > 63:
        print("Password is too long.")
    else:
        break
print("\n")
while True:
    saveSettings=input(f"Mode: {mode}\nSSID: {ssid}\nPassword: {passwd}\n\nSave these settings? (Y/N)").lower()
    if saveSettings in ["y","n"]:
        if saveSettings == "y":
            with open("config.json","w") as f:
                json.dump({'mode':mode,'ssid':ssid,'password':passwd},f)
                break 
        else:
            print("Saving settings aborted.")
            break 
    
