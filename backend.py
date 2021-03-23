import sys
from picamera import PiCamera
from os import system
import datetime
from time import sleep
import pyrebase
from PIL import Image
import Adafruit_DHT
import pymongo
import gc


import json
config = {
    "apiKey": "AIzaSyDibbqys6aPhIB1rFzOKbbWk986zlSumSA",
    "authDomain": "growroom-e5898.firebaseapp.com",
    "databaseURL": "https://growroom-e5898-default-rtdb.firebaseio.com",
    "projectId": "growroom-e5898",
    "storageBucket": "growroom-e5898.appspot.com",
    "seviceAccount": "serviceAccountKey.json"
    }
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 21
gc.enable()
tlminutes = 175200 #set this to the number of minutes you wish to run your timelapse camera
secondsinterval = 3600 #number of seconds delay between each photo taken
fps = 30 #frames per second timelapse video
numphotos = int((tlminutes*60)/secondsinterval) #number of photos to take
print("number of photos to take = ", numphotos)


#python3 workflow.py -i /home/pi/Hydroponic/images/0_A_p0.png -o /home/pi/Hydroponic/images -r results.json -w -D 'print'


#print("RPi started taking photos for your timelapse at: " + datetimeformat)

camera = PiCamera()
camera.resolution = (1024, 768)

#delete all photos in the Pictures folder before timelapse start

for i in range(numphotos):
    
    gc.collect(generation=2) 
    system('rm /home/pi/Hydroponic/images/*.jpg')
    system('rm /home/pi/Hydroponic/images/*.png')
    system('rm /home/pi/Hydroponic/images/*.json')
    dateraw= datetime.datetime.now()
    datetimeformat = dateraw.strftime("%Y-%m-%d_%H:%M")
    daytimeformat = dateraw.strftime("%Y-%m-%d")
    hourtimeformat = dateraw.strftime("%H:%M")
    camera.capture('/home/pi/Hydroponic/images/{}.jpg'.format(i))
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    print(humidity)
    if humidity is not None and temperature is not None:
        humid=humidity
        temp=temperature
        print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temp, humid))
    else:
       
        humid=0
        temp=0 
        print("Failed to retrieve data from humidity sensor")
    sys.argv = ["./plant_analyze.py",'-i/home/pi/Hydroponic/images/{}.jpg'.format(i), '-o/home/pi/Hydroponic/images', '-n/home/pi/Hydroponic/name.txt', '-D "print"']
    exec(open("./plant_analyze.py").read())
    

    arr = os.listdir('/home/pi/Hydroponic/images')
   
    
    arr.sort();
    plants = []
    growdata = []
    for x in arr:
        substring = "mask"
        if x.find(substring) != -1:
            #print(x)
            im = Image.open('/home/pi/Hydroponic/images/' + x)
            white = 0
            plant = 0

            for pixel in im.getdata():
                if pixel == (0): # if your image is RGB (if RGBA, (0, 0, 0, 255) or so
                    white += 1
                else:
                    plant += 1
            analyze = x.replace("_"+substring,'')
            sys.argv = ["./workflow.py",'-i/home/pi/Hydroponic/images/'+ analyze,'-o/home/pi/Hydroponic/images','-r./images/results_'+analyze+'.json','-w','-D/print']
            exec(open("./workflow.py").read())
           
            fileName = './images/results_'+analyze+'.json' 
            #f = open(fileName, "r")
            #print(f.read())
            #print('plant size is '+str(plant)+ " pixels")
            #jsonf=f.read()
            #y = eval(jsonf) 
            #print(json)
            #plants.append(y)
            
            #print(plants)
            with open(fileName, 'r') as j:
                contents = json.loads(j.read())
                contents["pixels"] = plant
                plants.append(contents)
            
    #print(plants) 
    firebase = pyrebase.initialize_app(config)
    storage = firebase.storage()
    database = firebase.database()
    data = {"Date": daytimeformat,"Time":hourtimeformat,"Temperature":"{0:0.1f}".format(temp),"Humidity":"{0:0.1f}".format(humid), "ImageURL":"gs://growroom-e5898.appspot.com/{}.jpg".format(i),"Plants": plants}
    
    #database.set(data)

    myclient = pymongo.MongoClient("mongodb+srv://alebor:Nxebjuxf14@cluster0.fgp5d.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    mydb = myclient["Plants"]
    mycol = mydb["Growdata"]
    
    
    
    x = mycol.insert_one(data)
    storage.child('{}.jpg'.format(i)).put('/home/pi/Hydroponic/images/{}.jpg'.format(i))

    gc.enable()
    sleep(secondsinterval)
print("Task Complete")
