import json
from dotenv import load_dotenv
from mqtt_bambulab import processMessage 

load_dotenv()

def run_test():
  i = 1
  with open("mqtt.log", "r", encoding="utf-8") as file:
    for line in file:
        print("row "+ str(i))
        i= i + 1
        processMessage(json.loads(line))


run_test()