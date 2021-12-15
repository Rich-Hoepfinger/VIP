# setup the periodic boundary
from __future__ import print_function
from yade import pack, plot
import math
import os
import sys

O.periodic = True
#x = 54.8e-3									#Size of the initial 2D box for 5000 particles
x = 31.03e-3									#Size of the initial 2D box for 2000 particles (I think)
Radius = 0.3e-3 						 		# Radius equal to 0.3mm - In the range of typical sand particle sizes
Number_of_disks = 2000
Max_shear_Strain = 20					 		# Maximum % of strain
friction = .5									# friciton varying [0.1,0.2.......0.5]
confining_stress = 500000						# Initial confining stress in kPa [100,200,.....500]

os.chdir('simoutputs')

# Looks through the directory and find the first simulation that has not been ran starting from the friction and
# confining stress defined and will automatically make and change parameters to meet the next sim criteria
def simLoop():
	global friction
	global confining_stress
	if friction >= .9 and confining_stress >= 600000:
		exit()
		sys.exit(0)
	directory = str(friction) + 'Sim' + str(confining_stress)
	if not os.path.exists(directory):
		directory = str(friction) + 'Sim' + str(confining_stress)
		os.mkdir(directory)
		os.chdir(directory)
		return [friction, confining_stress]
	else:
		if friction < .9:
			friction = friction + .1
		else:
			confining_stress = confining_stress + 100000
			friction = .1
		simLoop()

# Runs the method above
simLoop()

O.cell.hSize = Matrix3(x, 0, 0, 0, x, 0, 0, 0, 1)        	# Assigning box size
O.materials.append(FrictMat(young=70e9,poisson=0.3,frictionAngle=friction,density=2650e4,label='mat_spheres'))        # Properties of the spheres
sp=pack.SpherePack()
sp.makeCloud(minCorner=(0,0,0),maxCorner=(x,x,0),rRelFuzz=0.5,rMean=Radius,periodic=True,seed=1,num=Number_of_disks) 	# Generates Spheres randomly in space with no initial contacts, rRelFuzz=0 meaning all the paritcles have same radius -"Radius"
sp.toSimulation()

V_disks=Number_of_disks*(math.pi*(Radius**2))
V_box_2D=O.cell.hSize[0,0] * O.cell.hSize[1,1]

for b in O.bodies:
	b.state.blockedDOFs='zXY'               # The degrees of freedom in z-direction are constrained making sure the problem is purely 2D.

# Is the next thing run by the simulation every iteration until the consolidation stage is finished
O.engines = [
        ForceResetter(),
        InsertionSortCollider([Bo1_Sphere_Aabb()]),
        InteractionLoop(
                [Ig2_Sphere_Sphere_ScGeom()],
                #[Ip2_FrictMat_FrictMat_MindlinPhys(eta=0.5,krot=0.5)], #en=0.9,es=0.9,
                #[Law2_ScGeom_MindlinPhys_Mindlin(includeMoment=True)]
				[Ip2_FrictMat_FrictMat_FrictPhys()],
				[Law2_ScGeom_FrictPhys_CundallStrack()] #No rolling resistance, normal and tangential force calculated simply
        ),
        NewtonIntegrator(damping=.2),
	#Servo-controlled setup to achieve required consolidation
	PeriTriaxController(
                label='triax',
                goal=(-1*confining_stress, -1*confining_stress, 0),
                stressMask=3,
                # type of servo-control
                dynCell=True,
                maxStrainRate=(.05, .05, 0.),
                # wait until the unbalanced force goes below this value
                maxUnbalanced=2e-3,
                relStressTol=1e-3,
                # call this function when goal is reached and the packing is stable
                doneHook='consolidationFinished()'
        ),
        PyRunner(command='consData()', iterPeriod=100)
]

# Runs when the consolidation stage is finished
def consolidationFinished():
	plot.saveDataTxt(str(friction)+'Cons_result'+str(confining_stress)+'.txt')
	O.cell.velGrad = Matrix3(0, 0, 0, 0, 0, 0, 0, 0, 0)
	V_box_2D=O.cell.hSize[0,0] * O.cell.hSize[1,1]#Volume of the cell
	stress = -1*getStress(V_box_2D).trace() / 3.      #getStress gives the stress matrix-compression stress taken as positive
	print ('Finished, Isotropic Consolidation')
	plot.reset()
	O.save('Consolidated.yade')
	O.cell.velGrad = Matrix3(0, -0.01, 0, 0, 0, 0, 0, 0, 0)
	O.materials[0].frictionAngle = .5  # radians
	for i in O.interactions:
		i.phys.tangensOfFrictionAngle = tan(.5)
	O.engines = O.engines[0:4] + [PyRunner(command='checkDistorsion()', iterPeriod=100)]+[PyRunner(command='shearData()', iterPeriod=100)]
	triax.doneHook='checkDistorsion()'

# Checks to see if the box is sheared enough
def checkDistorsion():
	gamma=(O.cell.hSize[0,1]*100.0)/O.cell.hSize[1,1]
	# Runs when the box is sheared enough
	if abs(gamma) > Max_shear_Strain:
		plot.saveDataTxt(str(friction)+"Results"+str(confining_stress)+".txt")
		O.save('Sheared.yade')
		sys.exit(0)

# Adds the consolidation data to the plot variable
def consData():
  	V_box_2D=O.cell.hSize[0,0]*O.cell.hSize[1,1]
  	contactStress=getStress(V_box_2D)
  	e=(V_box_2D-V_disks)/V_disks
	# Keeps track of all the data that will be outputted to the files
  	plot.addData(
iter=O.iter,contactStress00=(contactStress[0,0]),contactStress01=(contactStress[0,1]),contactStress11=(contactStress[1,1]),voidratio=e
  )
	#plot.saveDataTxt('Cons_result.txt')

def shearData():
  	V_box_2D=O.cell.hSize[0,0]*O.cell.hSize[1,1]
	contactStress=utils.getStress(V_box_2D)
	stressxy=contactStress[0,1]
	#stressyy=contactStress[1,1]
	stressxx=contactStress[0,0]
	gamma=(O.cell.hSize[0,1]*100.0/O.cell.hSize[1,1])
	#void_ratio=(V_box_2D-V_disks) / V_disks
	#z=utils.avgNumInteractions(skipFree=True)
	#------------Stress Data--------------#
	#f=open("shear.txt","a")
	#print ("%0.9f %0.4f %0.4f %0.4f %0.5f" % (gamma,stressxy/1000.0,void_ratio,stressxx/1000.0,stressyy/1000.0),file=f)
	#f.close()
	#------------Fabric Data--------------#
	#FTS=utils.fabricTensor(splitTensor=False)[0]
	#f=open("fabric.txt","a")
	#print("%0.9f %0.4f %0.4f %0.4f %0.3f %0.5f %0.5f %0.5f" %(gamma, stressxy/1000.0,stressxx/1000.0,stressyy/1000.0,z, FTS[0,0],FTS[0,1],FTS[1,1]),file=f)
	#f.close()
	# What will be outputted to the results file
	plot.addData(gammaxaxis=gamma,sigmaxyyaxis=stressxy,sigmaxxxaxis=stressxx)


print ('void ratio:',(V_box_2D-V_disks)/V_disks,'dt:',0.5*utils.PWaveTimeStep())
O.dt=utils.PWaveTimeStep() #computes minimum critical time step for all spheres in a simulation
O.run()

