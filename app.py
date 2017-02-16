import schedule
import time

print("Meme analytics running")

def scan():
    print("I'm working...")

schedule.every(5).seconds.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)