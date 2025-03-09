import json
from mqtt_bambulab import processMessage 

def run_test():
  i = 1
  with open("mqtt4.log", "r", encoding="utf-8") as file:
    for line in file:
        print("Zeile "+ str(i))
        i= i + 1
        processMessage(json.loads(line))


run_test()