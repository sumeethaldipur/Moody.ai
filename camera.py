import cv2
from model.FER import FacialExpressionModel
import numpy as np
import time
from flask import *
import os
import uuid
import face_recognition
from db import conn

# defining face detector
face_cascade=cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
font = cv2.FONT_HERSHEY_SIMPLEX


video = cv2.VideoCapture()
def gen(cnn):
    video.open(0)            
    while True:
        ret, frame = video.read()
        try:
            GrayImg = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        except:
            continue
        faces = face_cascade.detectMultiScale(GrayImg, 1.32, 5)
        i=1
        for (x, y, w, h) in faces:
            roi_GrayImg = GrayImg[ y: y + h , x: x + w ]
            roi_Img = frame[ y: y + h , x: x + w ]
            RGBImg = cv2.cvtColor(roi_Img,cv2.COLOR_BGR2RGB)
            
            RGBImg= cv2.resize(RGBImg,(48,48))

            RGBImg = RGBImg/255.

            pred = cnn.predict_emotion(RGBImg)
            cv2.putText(frame, 'Person:'+str(i)+" Mood:"+pred, (x, y), font, 0.6, (0, 255, 0), 1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
            i+=1
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

def stop(cnn, user, folder):
    while True:
        flag = False
        ret, frame = video.read()
        try:
            gray_fr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_fr, 1.32, 5)
        except:
            continue
        if len(faces)==0:
            continue
        else:
            video.release()
            train = face_recognition.load_image_file(os.path.join(folder,user))
            train_face_encodings = face_recognition.face_encodings(train)[0]
            face_names = None 
            i=1
            face = []
            for (x, y, w, h) in faces:
                roi_GrayImg = gray_fr[ y: y + h , x: x + w ]
                roi_Img = frame[ y: y + h , x: x + w ]
            
                RGBImg = cv2.cvtColor(roi_Img,cv2.COLOR_BGR2RGB)
                
                RGBImg= cv2.resize(RGBImg,(48,48))

                RGBImg = RGBImg/255.                    
                test = cv2.cvtColor(roi_Img, cv2.COLOR_BGR2RGB)
                try:
                    face_encodings = face_recognition.face_encodings(test)[0]
                    valid = face_recognition.compare_faces([face_encodings], train_face_encodings)
                except:
                    video.open(0)
                    flag= True
                    break
                print(valid)
                pred = cnn.predict_emotion(RGBImg)
                if valid[0]:
                    face.append([i, pred])
                cv2.putText(frame, 'Person:'+str(i)+" Mood:"+pred, (x, y), font, 0.6, (0, 255, 0), 1)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
                i+=1
            if flag: continue
            name = str(uuid.uuid1()) + '.png' 
            os.chdir(r'C:\Users\Pritam\OneDrive\Desktop\Backend\static\images\capture')
            cv2.imwrite(name, frame)
            
            return [name,face]
        
def stop1(cnn, root): 
    while True:
        ret, frame = video.read()
        try:
            gray_fr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_fr, 1.32, 5)
        except:
            continue
        if len(faces)==0:
            continue
        else:
            video.release()
            i=1
            face = []
            for (x, y, w, h) in faces:
                roi_GrayImg = gray_fr[ y: y + h , x: x + w ]
                roi_Img = frame[ y: y + h , x: x + w ]

                RGBImg = cv2.cvtColor(roi_Img,cv2.COLOR_BGR2RGB)
                
                RGBImg= cv2.resize(RGBImg,(48,48))

                RGBImg = RGBImg/255.                    
                
                pred = cnn.predict_emotion(RGBImg)
                face.append([i, pred])
                cv2.putText(frame, 'Person:'+str(i)+" Mood:"+pred, (x, y), font, 0.6, (0, 255, 0), 1)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
                i+=1
            name = str(uuid.uuid1()) + '.png' 
            os.chdir(os.path.join(root, "static\images\capture"))
            cv2.imwrite(name, frame)

            return [name,face]
        
def validProfile(fname):
    print(fname)
    img = cv2.imread(fname)
    gray_fr = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_fr, 1.32, 5)
    if len(faces)==1:
        return True
    else:
        return False


def stop3(cnn, user, folder, root):
    while True:
        flag = False
        ret, fr = video.read()
        frame = cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(frame)
        encodings = face_recognition.face_encodings(frame, faces)
        if len(faces)==0:
            continue
        else:
            video.release()
            train = face_recognition.load_image_file(os.path.join(folder,user))
            known_face_encodings = face_recognition.face_encodings(train)[0]
            face_names = None 
            i=1
            face = []
            t = False
            for (t, r, b, l), face_encoding in zip(faces, encodings):
                valid = face_recognition.compare_faces([known_face_encodings], face_encoding)
                if(~valid[0]):
                    continue
                else:
                    roi_Img = frame[ t: b , l: r ]
                    RGBImg = cv2.cvtColor(roi_Img,cv2.COLOR_BGR2RGB)
                    print(valid)
                    RGBImg= cv2.resize(RGBImg,(48,48))
                    RGBImg = RGBImg/255.                    
                    pred = cnn.predict_emotion(RGBImg)
                    face.append(pred)
                    cv2.putText(fr,"Mood:"+pred, (l, t), font, 0.6, (0, 255, 0), 1)
                    cv2.rectangle(fr, (l, t), (r, b), (255, 0, 0), 1)
                    break
            name = str(uuid.uuid1()) + '.png' 
            os.chdir(os.path.join(root,"static\images\capture"))
            cv2.imwrite(name, fr)
            return [name, face]