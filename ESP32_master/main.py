from views import *
from yolov5_detect import Model_setup
import threading
import time

event=threading.Event()

def start_Update():
    th=threading.Thread(target=Update)
    th.start()
    print("Update threading set!")
    event.set()


if __name__=="__main__":
    #加载yolov5模型
    Model_setup()
    
    #重置GPIO口
    Send_Code(code="0")

    #开启轮询ESP32CAM线程
    start_Update()
    
    event.wait()

    #开启服务器
    myapp.run(host="0.0.0.0",port=8000)



