import requests
import cv2
import numpy as np

import json
import time

if __name__=="__main__":
    data2="1"
    while True:    
        with requests.get("http://192.168.43.246/temperature") as r:
            data=r.content
            json_data=json.loads(r.content)
            print(json_data)
        #data2="0" if data2=="1" else "1"
        with requests.post("http://192.168.43.246/control",data=data2) as r:
            res=r.content
            print(res)