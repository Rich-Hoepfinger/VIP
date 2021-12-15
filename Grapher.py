import matplotlib.pyplot as plt
import numpy as np
import os
import sys

friction = .1
confining_stress = 100000
contains = None

# Is a funciton so I can repeatedly call it
def mainloop():
  incrementGraphs()

  os.chdir("../simoutputs")
  # Iterates through the folder to find an existing simulation and checks to see if there is an existing graph for it
  while (not os.path.exists(str(friction) + "Sim" + str(confining_stress))) or checkResults():
    os.chdir("../")
    increment()
    incrementGraphs()
    os.chdir("../simoutputs")

  os.chdir(str(friction) + "Sim" + str(confining_stress))

  #opens the first file, reads the first line of text to find the index where all the data values are stored
  f1 = open(str(friction) + "Results" + str(confining_stress) + '.txt', 'r')
  headers = f1.readline().split()
  sigmaxxIndex = headers.index("sigmaxxxaxis") - 1
  gammaIndex = headers.index("gammaxaxis") - 1
  sigmayyIndex = headers.index("sigmaxyyaxis") - 1

  next(f1)

  gamma = []
  sigmaxx = []
  sigmaxy = []

  # Iterates through the .txt file, adding all the data to different lists
  for line in f1:
    values = [float(s) for s in line.split()]
    gamma.append(values[gammaIndex])
    sigmaxx.append(values[sigmaxxIndex])
    sigmaxy.append(values[sigmayyIndex])

  os.chdir("../../Graphs")
  os.mkdir(str(friction) + "Graphs" + str(confining_stress))
  os.chdir(str(friction) + "Graphs" + str(confining_stress))

  # plots the gamma and stressXY on a graph
  plt.title(str(friction) + " Friction and " + str(confining_stress) + " Confining Stress.")
  plt.xlabel('Gamma (%)')
  plt.ylabel('StressXY (N/m^2) * 10^-3')
  plt.plot(abs(np.array(gamma)), abs(np.array(sigmaxy)/1000.), label = str(friction) + " friction, " + str(confining_stress) + " confining stress", color = "black")
  plt.savefig(str(friction) + "GammaXYGraph" + str(confining_stress) + ".png")
  plt.clf()
  plt.cla()
  plt.close()

  # Plots the StressXY and StressXX on a graph
  plt.title(str(friction) + " Friction and " + str(confining_stress) + " Confining Stress.")
  plt.xlabel('StressXX (N/m^2) * 10^-3')
  plt.ylabel('StressXY (N/m^2) * 10^-3')
  plt.plot(abs(np.array(sigmaxx) / 1000.), abs(np.array(sigmaxy)/1000.),
           label=str(friction) + " friction, " + str(confining_stress) + " confining stress", color="orange")
  plt.savefig(str(friction) + "GammaXXGraph" + str(confining_stress) + ".png")
  plt.clf()
  plt.cla()
  plt.close()

  gamma = []
  sigmaxx = []
  sigmaxy = []

  os.chdir("../../")

# Checks to see if the graph file already exists.
def incrementGraphs():
  global friction
  global confining_stress
  os.chdir('Graphs')
  while (os.path.exists(str(friction) + "Graphs" + str(confining_stress))):
    if friction < .9:
      friction = friction + .1
    elif confining_stress < 5000000:
      confining_stress = confining_stress + 100000
      friction = .1
    elif friction >= .9 and confining_stress > 500000:
      sys.exit(0)
  return True

# Increments friction and confining stress by .1 and 1000 respectively
def increment():
  global friction
  global confining_stress
  if friction < .9:
    friction = friction + .1
  elif confining_stress < 5000000:
    confining_stress = confining_stress + 100000
    friction = .1
  elif friction >= .9 and confining_stress > 500000:
    sys.exit(0)

# Checks to see if the results file exists
def checkResults():
  global friction
  global confining_stress
  if not os.path.exists(str(friction) + "Results" + str(confining_stress) + '.txt'):
    return False
  else:
    return True

while friction < 1 or confining_stress < 600000:
  mainloop()
