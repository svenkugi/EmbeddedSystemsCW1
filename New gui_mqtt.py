import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style

import tkinter as tk
from tkinter import ttk
import urllib
import json
import requests
import paho.mqtt.client as mqtt
import pandas as pd #data manipulation
import numpy as np #number crunching



LARGE_FONT=("Verdana",12)
NORM_FONT=("Verdana",10)
SMALL_FONT=("Verdana",8)
style.use("fivethirtyeight")

##some global vars
refresh=9000 #refresh constant
defrange="1d" #default timeframe
dataLoad=True #used to control pause and resume
jsonData=0; #global data var
##
f=Figure(figsize=(12,6),dpi=50)
f1=Figure(figsize=(8,2),dpi=50)
a = f.add_subplot(411) #Presence
b = f.add_subplot(412) #Temp
c = f.add_subplot(413) #Luminosity
d = f.add_subplot(414) #Luminosity
a1=f1.add_subplot(111)

f.tight_layout()
f1.tight_layout()
pd.options.mode.chained_assignment = None #disable some PD warnings

global presence
global lux
global temperature
global humidity
global Time
global msgbox_block
global Time_temp

msgbox_block=False
presence=[]
lux=[]
humidity=[]
temperature=[]
Time=[]
Time_temp=0



def on_connect(client, userdata, flags, rc):
    #print(1)
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    
    client.subscribe("esys/RushB/Data")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    
    #print(msg.topic+" "+str(msg.payload))
    #print(2)
    jsonData = json.loads(msg.payload.decode('utf-8'))
    data=pd.DataFrame(jsonData)
    #print(data)
    myFunc(data)

def myFunc(x):
    global msgbox_block
    global Time_temp
    #data=pd.DataFrame(x)
    #print(x)
    data=x
    presence.append(data["Data"]["Presence"])
    #presence["datestamp"]=np.array(presence["time"]) #convert from unix date-time format
    Time.append(data["Time"]["Presence"])

       
    lux.append(data["Data"]["Brightness"])
    #presence["datestamp"]=np.array(presence["time"]) #convert from unix date-time format
    

    temperature.append(data["Data"]["AmbientTemperature"])
    #presence["datestamp"]=np.array(presence["time"]) #convert from unix date-time format

    humidity.append(data["Data"]["Humidity"])
    #presence["datestamp"]=np.array(presence["time"]) #convert from unix date-time format
    

    ##This section deals with data plotting and styling
   
    if(presence[-1]==1):
        Time_temp=Time_temp+3
        print(Time_temp)
        if(Time_temp>=60 and msgbox_block==False):
            popupmsg("You've been sitting for too long")
            
        
    else:
        Time_temp=0

    status=detect_presence(presence)#Check presence status vs threshold

    
    a.clear()
    a.plot_date(Time,presence,"#00A3E0",label="presence")
    a.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    

    b.clear()
    b.plot_date(Time,lux,"#00A3E0",label="lux")
    b.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)

    c.clear()
    c.plot_date(Time,temperature,"#00A3E0",label="temperature")
    c.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)

    d.clear()
    d.plot_date(Time,humidity,"#00A3E0",label="humidity")
    d.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    
    
    ##add titles
    
    #title_a = "Presence Monitor Status: "+str(status)+" "+str(data["data"]["presence"]) #Later change the str to detected or not detected
    title_a = "Presence Monitor Status: "+str(status) #Later change the str to detected or not detected
    title_c = "Temperate Status: "+str(temperature[-1])+" C"
    title_b = "Luminosity Status: "+str(lux[-1])+" Lux"
    title_d = "Humidity Status: "+str(humidity[-1])+" %"
    if(presence[-1]==1):
        a.set_title(title_a,color="green")
    else:
        a.set_title(title_a,color="red")
    b.set_title(title_b)
    c.set_title(title_c)
    d.set_title(title_d)
   
    ##Small plot
    a1.clear()
    a1.plot_date(Time,presence,"#00A3E0",label="presence")
    a1.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    title_a1 = "Presence Monitor Status: "+str(status)
    if(presence[-1]==1):
        a1.set_title(title_a1,color="green")
    else:
        a1.set_title(title_a1,color="red")
    
##    if("normal"==popup.state()):
##        print("window open")
##    
    if(msgbox_block==False):    
        if(temperature[-1]>30):
            popupmsg("Temperature too high!")
        if(lux[-1]<=5):
            popupmsg("Too dark. Turn on the lights")
        if(humidity[-1]>=50):
            popupmsg("Too humid. Turn on AC")
    #print(msgbox_block)
    f.canvas.draw()
    f1.canvas.draw()
    app.update_idletasks()
    app.update()
    msgbox_block==False

##def loadData(status):
##    global dataLoad
##
##    if status == "resume":
##        dataLoad = True
##
##    elif status == "pause":
##        dataLoad = False
    

def changeTime(time):
    global defrange
    global refresh
    defrange=time
    refresh=9000
        
    

def update(popup):
    global msgbox_block
    msgbox_block=False
    popup.destroy()
    f.canvas.draw()
    f1.canvas.draw()
    app.update_idletasks()
    app.update()
    client.loop_forever()


##Sensor status checker
    
def detect_presence(data):
    
    if (data[-1]==1):
        status="Detected"
        #lambda: popupmsg("Too dark!") 
    else:
        status="Not detected"
     
    
    return status
##END OF SENSOR STATUS CHECKER


  
##Custom popup message displayer##



def popupmsg(msg):
    global msgbox_block
    popup = tk.Tk()
    popup.wm_title("Warning!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="both", pady=10,padx=33, expand=True)
    B1 = ttk.Button(popup, text="Okay", command = lambda: update(popup))
    B1.pack()
    msgbox_block=True
    #popup.mainloop()
##end of popup message displayer##

def calibrate():
    client.publish("esys/RushB/User", "calibrate")

    
class MonitorApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "MonitorApp") #add window title
        #tk.Tk.iconbitmap(self,default="icon.ico") add icon
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)       
        self.frames = {}

        for K in (ViewLess,ViewAll):

            frame = K(container, self)

            self.frames[K] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(ViewLess)
    def show_frame(self, cont):
        for frame in self.frames.values():
            frame.grid_remove()
        frame = self.frames[cont]
        frame.grid()
        frame.winfo_toplevel().geometry("")

    
        
class ViewAll(tk.Frame):

    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        
        ##Set up various panels as frames
        controlPanel =tk.Frame(self,width=1230,height=20) #control panel
        graphPanel=tk.Frame(self,width=1230,height=700) #graph panel
        controlPanel.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        graphPanel.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=True)
        
        ##Panel labels
        #graphLabel = tk.Label(graphPanel, text="Sensor Outputs", font=LARGE_FONT)
        #controlLabel=tk.Label(controlPanel,text="Control Panel",font=LARGE_FONT)
        #graphLabel.pack(side=tk.TOP)
        #controlLabel.pack(side=tk.TOP)

        ##control pannel buttons
        messageB=ttk.Button(controlPanel,text="Warning test",command=lambda:popupmsg("Warning test"))
        messageB.pack(side=tk.LEFT)

        #pauseB = ttk.Button(controlPanel,text="Pause",command=lambda:loadData("pause"))
        #resumeB = ttk.Button(controlPanel,text="Resume",command=lambda:loadData("resume"))
        
        #pauseB.pack()
        #resumeB.pack()

        viewLess=ttk.Button(controlPanel,text="View Less",
                            command=lambda:controller.show_frame(ViewLess))
        viewLess.pack(side=tk.RIGHT)

        calibrateB=ttk.Button(controlPanel,text="Calibrate",command=lambda:calibrate())
        calibrateB.pack(side=tk.RIGHT)
        
        ##Set up Plot Canvases       
        canvas_btc = FigureCanvasTkAgg(f,graphPanel)#sensor canvas
        canvas_btc.get_tk_widget().config(width=1000,height=720)
        canvas_btc.show()
##        toolbar = NavigationToolbar2TkAgg(canvas_btc,graphPanel)
##        toolbar.update()
##        toolbar.pack(side=tk.BOTTOM)
        canvas_btc.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=False)     
        canvas_btc._tkcanvas.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        ##Set up meny container Frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        

class ViewLess(tk.Frame):
    def __init__(self, parent,controller):#initialise stuff args and kwargs
        
        tk.Frame.__init__(self, parent)      
        
                
        ##Set up various panels as frames
        controlPanel =tk.Frame(self,width=650,height=20) #control panel
        graphPanel=tk.Frame(self,width=650,height=330) #graph panel
        controlPanel.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        graphPanel.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=True)
        
        ##Panel labels
##        graphLabel = tk.Label(graphPanel, text="Sensor Outputs", font=LARGE_FONT)
##        controlLabel=tk.Label(controlPanel,text="Control Panel",font=LARGE_FONT)
##        graphLabel.pack(side=tk.TOP)
##        controlLabel.pack(side=tk.TOP)

        ##control pannel buttons
        messageB=ttk.Button(controlPanel,text="Warning test",command=lambda:popupmsg("Warning test"))
        messageB.pack(side=tk.LEFT)

        #pauseB = ttk.Button(controlPanel,text="Pause",command=lambda:loadData("pause"))
        #resumeB = ttk.Button(controlPanel,text="Resume",command=lambda:loadData("resume"))
        
        #pauseB.pack()
        #resumeB.pack()

        viewAll=ttk.Button(controlPanel,text="View all",
                            command=lambda:controller.show_frame(ViewAll))
        viewAll.pack(side=tk.RIGHT)

        calibrateB=ttk.Button(controlPanel,text="Calibrate",command=lambda:calibrate())
        calibrateB.pack(side=tk.RIGHT)
        
        ##Set up Plot Canvases       
        canvas_btc = FigureCanvasTkAgg(f1,graphPanel)#sensor canvas
        canvas_btc.get_tk_widget().config(width=800,height=300)
##        canvas_btc.show()
##        toolbar = NavigationToolbar2TkAgg(canvas_btc,graphPanel)
##        toolbar.update()
##        toolbar.pack(side=tk.BOTTOM)
        canvas_btc.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=True)     
        canvas_btc._tkcanvas.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        ##Set up meny container Frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

app = MonitorApp()
#app.geometry("1280x720")
print(1)      
client = mqtt.Client()
print(2)
client.on_connect = on_connect
print(3)
client.on_message = on_message
print(4)    
client.connect("192.168.4.2", 1883, 60)
client.loop_forever()
print(5)
        



        
