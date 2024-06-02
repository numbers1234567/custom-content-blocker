# Python file to run both the post_prc.py and main.py locally.

import time
import subprocess

with open("post_prc.log", "w+") as pp:
    i = subprocess.Popen(["python", "post_prc.py"], stdout=pp, stderr=subprocess.STDOUT)
    print("Started post processor.")
time.sleep(10) # Or however much time it takes to load stuff
with open("uvicorn_api.log", "w+") as ua:
    subprocess.Popen(["uvicorn", "main:app", "--reload"], stdout=ua, stderr=subprocess.STDOUT)
    print("Started API.")