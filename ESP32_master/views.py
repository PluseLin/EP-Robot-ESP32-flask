from flask import *
from flask_bootstrap import *
from flask_sqlalchemy import *

import requests
import threading
import json

from yolov5_detect import *

myapp=Flask(__name__)
bootstrap=Bootstrap()
db=SQLAlchemy()
bootstrap.init_app(myapp)

myapp.config["SECRET_KEY"]="sjadlajwdiljdilawjd"
# 数据库信息 格式:mysql://user:password@localhost/database
db_uri='mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(
    'root','012704','localhost','3306','robot'
)
myapp.config['SQLALCHEMY_DATABASE_URI'] = db_uri
myapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
myapp.config['TEMPLATES_AUTO_RELOAD'] = True

db.init_app(myapp)
db.app=myapp

ip="192.168.43.154"

TEMP_URL="http://{}/temperature".format(ip)
IMAGE_URL="http://{}/capture".format(ip)
CTRL_URL="http://{}/control".format(ip)

temp=0.0
img=b""
send_flag=0
reset_flag=1
has_detected=True

class Disaster(db.Model):
    __tablename__="disaster"
    id=db.Column(db.Integer,primary_key=True)
    d_time=db.Column(db.DateTime())
    d_type=db.Column(db.String(255))
    d_picname=db.Column(db.String(255))
    def __repr__(self) -> str:
        return "{{id:{0},d_time:{1},d_type:{2}}}".format(
            self.id,self.d_time,self.d_type
        )

def Disaster_Insert(disa:Disaster):
    db.session.add(disa)
    db.session.commit()

def Disaster_Query_All():
    return Disaster.query.all()

def Update():
    global temp,img,send_flag,reset_flag,has_detected
    while True:
        try:
            with requests.get(TEMP_URL) as r:
                json_data=json.loads(r.content)
                temp=json_data["temp"]
        except Exception as e:
            #raise e
            print("GET from {} fail!".format(TEMP_URL))
        try:
            with requests.get(IMAGE_URL,stream=True) as r:
                img=r.content
        except Exception as e:
            print("GET from {} fail!".format(IMAGE_URL))
        if not has_detected:
            detect_result=detect(img,srctype="bytes")
            if(detect_result["fire"]>=1 or detect_result["smoke"]>=1):
                d_type=""
                d_type+="fire " if detect_result["fire"]>=1 else ""
                d_type+="smoke" if detect_result["smoke"]>=1 else ""
                print("detected fire or smoke!",detect_result)
                send_flag=1
                has_detected=True
                #添加到数据库中
                disa=Disaster(
                    d_time=detect_result["curtime"],
                    d_type=d_type,
                    d_picname=detect_result["filename"]
                )
                Disaster_Insert(disa)

        if(send_flag==1):
            Send_Code()
            send_flag=0
        if(reset_flag==1):
            Send_Code("0")
            reset_flag=0
            has_detected=False

def GetImage():
    while True:
        yield(
            b'--frame\r\n'+
            b'Content-Type:image/jpeg\r\n\r\n'+img+b'\r\n'
        )

def GetTemp():
    while True:
        yield str(temp)

@myapp.route("/image",methods=['GET','POST'])
def image():
    return Response(
        GetImage(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@myapp.route("/temp",methods=['GET','POST'])
def temperature():
    return Response(
        GetTemp(),
    )

def Send_Code(code="1"):
    try:
        with requests.post(CTRL_URL,code,timeout=3) as r:
            res=r.content
    except Exception as e:
        print("POST to {} fail!".format(CTRL_URL))

@myapp.route("/",methods=['GET','POST'])
def index():
    global send_flag
    global reset_flag
    data={}
    data["temp"]=temp
    json_data=request.get_json()
    if json_data is not None:
        ret_data={}
        if json_data["action"]=="stop_routing":
            send_flag=1
        if json_data["action"]=="reset_port":
            reset_flag=1
        if json_data["action"]=="get_temp":
            ret_data["data"]="当前环境温度：{}".format(temp)
        return jsonify(ret_data)
        
    return render_template(
        "index.html",
        data=data
    )

@myapp.route("/record",methods=['GET','POST'])
def record():
    data={"records":[]}
    for each in Disaster_Query_All():
        data["records"].append({
            "id":each.id,
            "d_time":each.d_time,
            "d_type":each.d_type,
            "d_picname":"image/"+each.d_picname
        })
    return render_template(
        "record.html",
        data=data
    )