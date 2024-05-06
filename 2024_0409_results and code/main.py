import pyvisa
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from os import mkdir
from os.path import exists


def get_instrument(
    rm,
    cache_file,
    cache_code,
    write_termination= '\n', read_termination='\n'
):
    try:
        with open(cache_file, "r") as f:
            for line in f.readlines():
                code, resource_name = line.strip('\n').split(" ")
                if code == cache_code:
                    instrument = rm.open_resource(resource_name,write_termination= write_termination, read_termination=read_termination)
                    return instrument
            raise FileNotFoundError
    except FileNotFoundError:
        while True:
            try:
                print(f"get instrument for {cache_code}")
                resources_list = rm.list_resources()
                for idx, resource in enumerate(resources_list):  
                    print(f"{idx} : {resource}")
                    
                idx= int(input("input the index of resource to access : "))
                instrument = rm.open_resource(resources_list[idx],write_termination= write_termination, read_termination= read_termination)
                
                with open("cache.txt", "a") as f:
                    f.write(f"{cache_code} {resources_list[idx]}\n")
                break                
            except IndexError:
                continue
        
        return instrument
        
        
rm = pyvisa.ResourceManager()
oscilloscope =  get_instrument(rm, "cache.txt", "Oscilloscope")

oscilloscope.write("*IDN?")
print(f"oscilloscope id : {oscilloscope.read()}")




Number_of_data = 1000

result_dicts = []
oscilloscope.write("SYSTem:AUToscale 1") #Enable AUToset action


if exists("figs") is False:
    mkdir("figs")

oscilloscope.write(":WAVeform:SOURce CHANnel1") # set channel to 1
oscilloscope.write(":WAVeform:MODE NORMal") #Read the data on the screen
oscilloscope.write(":WAVeform:FORMat ASCii") #Format into csv
oscilloscope.write(f":WAVeform:POINts {Number_of_data}") #Grab 1000 points, which are maximum number
oscilloscope.write("WAVeform:DATA?") #Get data
error_data = list(map(lambda x: float(x),oscilloscope.read().split(','))) #Get data from amplified signal
oscilloscope.write(":WAVeform:XINCrement?")
time_increment = float(oscilloscope.read()) #Get time difference between points of amplified data

result_dict = {
    'error_data' :error_data,
    'time_increment' : time_increment,
    }
result_dicts.append(result_dict) #build a result list

y1 = result_dict["error_data"]
step1 = result_dict["time_increment"]
x1 = np.array(range(Number_of_data))*step1

stdev = np.std(np.array(y1))

figsize = (32,4)
fig = plt.figure(figsize = figsize)
ax = fig.add_subplot(1,1,1)

ax.plot(x1,y1, 'k-')
ax.set_xlabel("time [s]")
ax.set_ylabel("result [V]")

for index in range(100):
    if exists(f"figs/figure{index}.png") is False:
        break

fig.savefig(f"figs/figure{index}.png")
plt.close(fig)
try:
    with open("results.txt", "a") as f:
        f.write(f"{index} : {stdev} V\n")
        
except FileNotFoundError:
    with open("results.txt", "w") as f:
        f.write(f"{index} : {stdev} V\n")

del fig

    


