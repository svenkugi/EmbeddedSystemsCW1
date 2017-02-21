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
import pandas as pd #data manipulation
import numpy as np #number crunching

##define font parameters
LARGE_FONT=("Verdana",12)
NORM_FONT=("Verdana",10)
SMALL_FONT=("Verdana",8)
style.use("fivethirtyeight")
LIMIT =100

##declare subplots, figures

##Large view plots here
f=Figure(figsize=(12,6),dpi=50)
a = f.add_subplot(411) #Presence
b = f.add_subplot(412) #Temp
c = f.add_subplot(413) #Luminosity
d = f.add_subplot(414) #Luminosity
f.tight_layout()

##Compact view plot here
f1=Figure(figsize=(8,2),dpi=50)
a1=f1.add_subplot(111)
f1.tight_layout()

pd.options.mode.chained_assignment = None #disable some PD warnings
    
 

def update(popup):
    print("called")
    popup.destroy()
    app.update_idletasks()
    app.update()

##Sensor status checker (used to modify live status label)
    
def detect_presence(data):
    
    if (data[-1]==1): ##check last element of presence array for absence or presence
        status="Detected"
    else:
        status="Not detected"  
    return status

  
##Custom popup message displayer##


def popupmsg(msg):
    ##Set up message box GUI
    popup = tk.Tk()
    popup.wm_title("Warning!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="both", pady=10,padx=33, expand=True)
    B1 = ttk.Button(popup, text="Okay", command = lambda:update(popup))
    B1.pack()
    popup.mainloop()
##end of popup message displayer##

def animate(i):
    ##establish link to cloud and download JSON object, format using pandas
    dataLink='http://embeddedsystems.azurewebsites.net/scripts/request.php'
    data = urllib.request.urlopen(dataLink)
    data = data.read().decode("utf-8") 
    data = json.loads(data)
    data = pd.DataFrame(data)
    ##Use numpy to extract specific data points from JSON object (capacity set by limit)
    Time=np.array(data["time_data"])[1:LIMIT]
    presence=np.array(data["presence"])[1:LIMIT]
    lux=np.array(data["brightness"])[1:100]
    temperature=np.array(data["temperature"])[1:LIMIT]
    humidity=np.array(data["humidity"])[1:LIMIT]
    
    ##This section deals with data plotting and styling
    
    status=detect_presence(presence)#Check presence status vs threshold

    ##subplot a) presence
    a.clear()
    a.plot_date(Time,presence,"#00A3E0",label="presence")
    a.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    ##subplot b) luminosity
    b.clear()
    b.plot_date(Time,lux,"#00A3E0",label="lux")
    b.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    ##subplot c) temperature
    c.clear()
    c.plot_date(Time,temperature,"#00A3E0",label="temperature")
    c.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    ##subplot d) humidity
    d.clear()
    d.plot_date(Time,humidity,"#00A3E0",label="humidity")
    d.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    ##add titles
    title_a = "Presence Monitor Status: "+str(status) #Later change the str to detected or not detected
    title_c = "Temperate Status: "+temperature[-1]+" Lux"
    title_b = "Luminosity Status: "+lux[-1]+" C"
    title_d = "Humidity Status: "+humidity[-1]+" %"
    a.set_title(title_a)
    b.set_title(title_b)
    c.set_title(title_c)
    d.set_title(title_d)
   
    ##Small view plot (just presence)
    a1.clear()
    a1.plot_date(Time,presence,"#00A3E0",label="presence")
    a1.legend(bbox_to_anchor=(0,1.02,1,1.102),loc=3,
                             ncol=2,borderaxespad=0)
    title_a1 = "Presence Monitor Status: "+str(status)
    a1.set_title(title_a1)
        

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
        ##Set up Buttons
        viewLess=ttk.Button(controlPanel,text="View Less",
                            command=lambda:controller.show_frame(ViewLess))
        viewLess.pack(side=tk.RIGHT)
        calibrateB=ttk.Button(controlPanel,text="Calibrate",command=lambda:calibrate())
        calibrateB.pack(side=tk.RIGHT)
        
        ##Set up Plot Canvases       
        canvas_btc = FigureCanvasTkAgg(f,graphPanel)#sensor canvas
        canvas_btc.get_tk_widget().config(width=1000,height=720)
        canvas_btc.show()
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
        
        ##Set up Buttons
        viewAll=ttk.Button(controlPanel,text="View all",
                            command=lambda:controller.show_frame(ViewAll))
        viewAll.pack(side=tk.RIGHT)
        calibrateB=ttk.Button(controlPanel,text="Calibrate",command=lambda:calibrate())
        calibrateB.pack(side=tk.RIGHT)
        
        ##Set up Plot Canvases       
        canvas_btc = FigureCanvasTkAgg(f1,graphPanel)#sensor canvas
        canvas_btc.get_tk_widget().config(width=800,height=300)
        canvas_btc.get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=True)     
        canvas_btc._tkcanvas.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        ##Set up meny container Frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        

        
        
                   
app = MonitorApp()
ani2 = animation.FuncAnimation(f1,animate,interval=2000)
ani1 = animation.FuncAnimation(f,animate,interval=2000)
app.mainloop()

