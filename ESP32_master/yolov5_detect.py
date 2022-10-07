import os
import platform
import time
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadBytes, LoadStreams, LoadImages
from utils.general import (
    check_img_size, non_max_suppression, 
    scale_coords, xyxy2xywh, plot_one_box)
from utils.torch_utils import select_device,time_synchronized

import requests

'''
input:  img:图像编码
output  result:各类检测结果
'''

class opt:
    agnostic_nms=False
    augment=False
    classes=None
    conf_thres=0.4
    device='0'
    img_size=640
    iou_thres=0.5
    output='.\\static\\image'
    save_txt=False
    update=False
    weights=['.\\best.pt']
    webcam=False
    half=False
    device=None
    names=None
    colors=None

model = None
img=None

detect_target=["smoke","fire"]

'''
input:  img(str):图像路径
output  result(dict):各类检测结果
                smoke:  烟雾
                fire:   火焰
'''


def Model_setup():
    global model,img
    # Initialize
    opt.device = select_device('0')
    if(not os.path.exists(opt.output)):
        os.makedirs(opt.output)
    opt.half = opt.device.type != 'cpu'  # half precision only supported on CUDA

    print(opt.device)

    # Load model
    model = attempt_load(opt.weights, map_location=opt.device)  # load FP32 model
    imgsz = check_img_size(opt.img_size, s=model.stride.max())  # check img_size
    if opt.half:
        model.half()  # to FP16

    # Get names and colors
    opt.names = model.module.names if hasattr(model, 'module') else model.names
    opt.colors = [[random.randint(0, 255) for _ in range(3)] for _ in range(len(opt.names))]

    img = torch.zeros((1, 3, imgsz, imgsz), device=opt.device)  # init img
    _ = model(img.half() if opt.half else img) if opt.device.type != 'cpu' else None  # run once

    print("Model setup finished!")

def detect(source,srctype="other"):
    # Set Dataloader
    vid_path, vid_writer = None, None
    view_img,save_img=False,False
    imgsz = check_img_size(opt.img_size, s=model.stride.max())

    result={}
    for each in opt.names:
        result[each]=0

    if opt.webcam:
        view_img = True
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz)
    elif srctype=="other":
        save_img = True
        dataset = LoadImages(source, img_size=imgsz)
    else:
        save_img = True
        dataset = LoadBytes(source, img_size=imgsz)

    # Run inference
    t0 = time.time()

    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(opt.device)
        img = img.half() if opt.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]

        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if opt.webcam:  # batch_size >= 1
                p, s, im0 = path[i], '%g: ' % i, im0s[i].copy()
            else:
                p, s, im0 = path, '', im0s

            #save_path = str(Path(opt.output) / Path(p).name)
            #save_path=os.path.join(opt.output,"{}.jpg".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())))
            curtime=time.strftime("%Y_%m_%d__%H_%M_%S",time.localtime())
            filename="{}.jpg".format(curtime)
            save_path=opt.output+"\\"+filename
            result["curtime"]=curtime
            result["filename"]=filename
            #print(os.path.abspath(save_path))
            #print(save_path)
            #txt_path = str(Path(opt.output) / Path(p).stem) + ('_%g' % dataset.frame if dataset.mode == 'video' else '')
            txt_path=".\\output.txt"
            s += '%gx%g ' % img.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += '%g %ss, ' % (n, opt.names[int(c)])  # add to string
                    result[opt.names[int(c)]]=int("%g" % (n))

                # Write results
                for *xyxy, conf, cls in det:
                    if opt.save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        with open(txt_path + '.txt', 'a') as f:
                            f.write(('%g ' * 5 + '\n') % (cls, *xywh))  # label format

                    if save_img or view_img:  # Add bbox to image
                        label = '%s %.2f' % (opt.names[int(cls)], conf)
                        plot_one_box(xyxy, im0, label=label, color=opt.colors[int(cls)], line_thickness=3)
                        # plot_one_box(xyxy, im0, label=None, color=colors[int(cls)], line_thickness=3)  # 只画框，不画类别 置信度

            # Print time (inference + NMS)
            #print('%sDone. (%.3fs)' % (s, t2 - t1))

            # Stream results
            if view_img:
                cv2.imshow(p, im0)
                if cv2.waitKey(1) == ord('q'):  # q to quit
                    raise StopIteration

            # Save results (image with detections)
            
            flag=False
            for each in detect_target:
                if(result[each]>=1):
                    flag=True
                    break

            if save_img and flag==True:
                if dataset.mode == 'images':
                    succ=cv2.imwrite(os.path.abspath(save_path), im0)
                else:
                    if vid_path != save_path:  # new video
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  # release previous video writer

                        fourcc = 'mp4v'  # output video codec
                        fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*fourcc), fps, (w, h))
                    vid_writer.write(im0)

    if opt.save_txt or save_img:
        #print('Results saved to %s' % Path(opt.output))
        if platform.system() == 'Darwin' and not opt.update:  # MacOS
            os.system('open ' + save_path)
    
    return result
    #print('Done. (%.3fs)' % (time.time() - t0))

def test1():
    with requests.get('http://192.168.43.154/capture',stream=True) as r:
        data=r.content
    res=detect(data,srctype='bytes')
    print(res)

if __name__=="__main__":
    Model_setup()
    test1()
    # print("")
    # while True:
    #     img_addr=input("请输入图片地址：")
    #     detect(img_addr)
        