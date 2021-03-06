import numpy as np
import matplotlib.pyplot as plt
import plotset as ps
import sys, getopt
import time

# Gravitational Accelerations

def atest(r,R,M):
	"""Gravitational accleration of test masses"""
	n = len(M)
	accel = 0
	for i in range(0,n):
		mag = (sum((r-R[i,:])**2))**0.5
		accel += -M[i]*(r-R[i,:])/mag**3
	return accel

def agalaxy(r,R,M):
	"""Gravitational accleration of a galaxy due to the other"""
	mag = (sum((r-R)**2))**0.5
	accel = -M*(r-R)/mag**3
	return accel

# Runge-Kutta Method

def RKstep(h,v,r,R,M,a):
	# Runge-Kutta Algorithm
	r_1 = r
	v_1 = v
	a_1 = a(r,R,M)

	r_2 = r + 0.5*v_1*h
	v_2 = v + 0.5*a_1*h
	a_2 = a(r_2,R,M)

	r_3 = r + 0.5*v_2*h
	v_3 = v + 0.5*a_2*h
	a_3 = a(r_3,R,M)

	r_4 = r + v_3*h
	v_4 = v + a_3*h
	# a4 = a(r_4,R,M)

	r_f = r + (h/6)*(v_1+2*v_2+2*v_3+v_4)
	# Do not require velocities in simulation so steps removed for efficiency
	# v_f = v + (h/6)*(a_1+2*a_2+2*a_3+a_4)
	return r_f


class Particle(object):

	def __init__(self,r,v):
		"""Defines initial parameters (position, velocity)"""
		self.R = r
		self.V = v

	def initialstep(self,h,galaxy_M,galaxy_r,RK4step):
		"""Initial step taking to obtain r_(1) from initial values"""
	
		if not RK4step:
			# Using Taylor expansion about t = 0 to 2nd order
			self.Rnew = self.R + h*self.V + 0.5*atest(self.R,galaxy_r,galaxy_M)*h**2
		else:
			self.Rnew = RKstep(h,self.V,self.R,galaxy_r,galaxy_M,atest)

		self.Rold = self.R
		self.R = self.Rnew

	def verletstep(self,h,galaxy_M,galaxy_r):
		"""Verlet Integration algorithm"""

		# Note: Must be performed after a single call of the initialstep function

		self.Rnew = 2*self.R-self.Rold+(h**2)*atest(self.R,galaxy_r,galaxy_M)

		self.Rold = self.R
		self.R = self.Rnew

		# Do not need velocity in simulation so comment out to increase speed

		# self.V = (self.Rnew-self.Rold)/(2*h)

	def returnvalues(self):
		"""Returns position vector for plotting purposes"""
		return self.R



class Galaxy(object):

	def __init__(self,m,r,v):
		"""Defines initial parameters (position, velocity) and the mass of the object"""
		self.M = m
		self.R = r
		self.V = v

	def initialstep(self,h,galaxy_M,galaxy_r,RK4step):
		"""Initial step taking to obtain r_(1) from initial values"""

		if not RK4step:
			self.Rnew = self.R + h*self.V + 0.5*agalaxy(self.R,galaxy_r,galaxy_M)*h**2
		else:
			self.Rnew = RKstep(h,self.V,self.R,galaxy_r,galaxy_M,agalaxy)

		self.Rold = self.R
		self.R = self.Rnew

	def verletstep(self,h,galaxy_M,galaxy_r):
		"""Verlet Integration algorithm"""

		# Note: Must be performed after a single call of the initialstep function

		self.Rnew = 2*self.R-self.Rold+(h**2)*agalaxy(self.R,galaxy_r,galaxy_M)

		self.Rold = self.R
		self.R = self.Rnew

		# Do not need velocity in simulation so comment out to increase speed

		# self.V = (self.Rnew-self.Rold)/(2*h)

	def createring(self,n_particles, radius, co):
		# Create a ring of test particles at given radius and density
		if co:
			sign = -1
		else:
			sign = 1
		particles = []
		for j in range(0,len(radius)):
			R = np.zeros((2,n_particles[j]))
			V = np.zeros((2,n_particles[j]))
			v_init = radius[j]**(-0.5)
			angle = 2*np.pi/n_particles[j]
			for i in range(0,n_particles[j]):
				R[:,i] = [self.R[0]+radius[j]*np.cos(i*angle),self.R[1]+radius[j]*np.sin(i*angle)]
				V[:,i] = [self.V[0]-sign*v_init*np.sin(i*angle),self.V[1]+sign*v_init*np.cos(i*angle)]
			for k in range(0,n_particles[j]):
				particles.append(Particle(R[:,k],V[:,k]))
		return particles

	def returnvalues(self):
		return self.R


def checkparabolic(e):
	# Since e is entered as a float must check for region around e = 1
	if 1.001 > e > 0.999:
		return True
	else:
		return False

def orbit(f,e,angle):
	# Radial equation of orbits of eccentricity e
	# f is distance of closest approach
	# Define orbital parameters semi-latus rectum and semi-major axis
	r0 = f*(1+e)

	r = r0/(1+e*np.cos(angle))
	R = np.array((r*np.cos(angle),r*np.sin(angle)))

	if checkparabolic(e):
		# Parabola has E = 0
		v = (2/r)**0.5
		# dy/dx = -2f/y from equation of parabola
		theta = np.arctan(-2*f/R[1])
	elif e < 1 and e >= 0:
		# Ellipictal/circular orbit
		# energy E = -A/2a => find v
		a = r0/(1-e**2)
		v = (2/r-1/a)**0.5
		
		# Equation of ellipse ((x+ae)/a)**2+(y/b)**2 = 1
		b = r0*(1-e**2)**(-0.5)
		dydx = -((b/a)**2)*(R[0]+a*e)/R[1]
		theta = np.arctan(dydx)
	elif e > 1:
		# Hyperbolic orbit
		# energy E = -A/2a => find v
		a = r0/(1-e**2)
		v = (2/r-1/a)**0.5

		# Equation of hyperbola ((x+ea)/a)**2-(y/Y)**2 = 1
		Y = r0*(e**2-1)**(-0.5)
		dydx = ((Y/a)**2)*(R[0]+a*e)/R[1]
		theta = np.arctan(dydx)
	else:
		print("\nIncorrect value of eccentricity used, program terminated!\n")
		sys.exit()
	V = np.array((v*np.cos(theta),v*np.sin(theta)))
	return R,V


def numstr(i):
	# Function to make all number strings (0-999) be 3 figures long
	if i < 10:
		string = '00' + str(i)
	if i < 100 and i >= 10:
		string = '0' + str(i)
	if i >= 100:
		string = str(i)
	return string


def densitytoindex(len_r, densities,j):
	# Returns the index of the first particle in each ring of the orbiting test masses
	for i in range(len_r):
		if j >= sum(densities[:i]) and j < sum(densities[:(i+1)]):
			return sum(densities[:i])


def plottr(h, len_r, densities, rec_data, N, rec_n):
	# Produces a plot of change in radius against time
	t = h*np.linspace(0,N,N/rec_n)
	R = (rec_data[0,:,:]**2+rec_data[1,:,:]**2)**0.5
	for j in range(len(rec_data[0,:,0])):
		index = densitytoindex(len_r,densities,j)
		deltaR = R[j,:]-R[index,0]
		plt.plot(t,deltaR, 'k-')
	ylabelstr = u"\u0394"+'r / arb. units'
	ps.plotset(xlabel = 't / arb. units', ylabel = ylabelstr, minticks = True, sciaxis = 'y')
	boxstr = 'h = '+ str(h)
	plt.figtext(0.2, 0.8, boxstr, bbox = dict(facecolor = 'none', edgecolor = 'k', pad = 15.0))
	savepath = ps.getPath() + '/plots/radiustime_nork4.png'
	plt.savefig(savepath)
	plt.clf()

def orbittype(e):
	# Returns a string describing the type of orbit 
	if checkparabolic(e):
		return 'Parabolic'
	elif e < 1 and e >= 0:
		return 'Ellipictal'
	elif e > 1:
		return 'Hyperbolic'

def plotpos(rec_data1, rec_data2, N, rec_n, f, e, fixed, time, add_len = 5, frames = 1):
	# Creates a directory full of (N/frames*rec_n) plots showing the positions of all objects in the problem
	# Plots are in CoM frame of the initially stationary galaxy
	savedir = ps.savedir()
	limit = f + add_len
	for i in range(int(N/(frames*rec_n))):
		k = frames*i
		for j in range(len(rec_data1[0,:,0])):
			plt.plot(rec_data1[0,j,k],rec_data1[1,j,k], 'ko', markersize = 1)
		plt.plot(rec_data2[0,0,k],rec_data2[1,0,k],'ro')
		plt.plot(rec_data2[0,1,:k],rec_data2[1,1,:k],'b-')
		ps.plotset(xlim = [rec_data2[0,0,k]-limit,rec_data2[0,0,k]+limit], ylim = [rec_data2[1,0,k]-limit,rec_data2[1,0,k]+limit], xlabel = 'x / arb. units', ylabel = 'y / arb. units', minticks = True, eqaspect = True)
		titlestr = orbittype(e)+', e = '+str(e)+', f = '+str(f)
		plt.title(titlestr)
		# Lines used on my home PC to reduce file size, .jpg extension not supported at MCS
		# savepath = savedir + '/' + numstr(i) + '.jpg'
		# plt.savefig(savepath, quality = 50)
		savepath = savedir + '/' + numstr(i) + '.png'
		plt.savefig(savepath)
		plt.clf()
	# Create a text file containing important parameters for reference
	filepath = savedir + "/log.txt"
	f = open(filepath,"w")
	args = [fixed, N, rec_n, f, e, time]
	textstr = '\n\nFixed =\t\t{0}\nN =\t\t{1}\nrec_n =\t\t{2}\nf =\t\t{3}\ne =\t\t{4}\nT =\t\t{5}'.format(*args)
	f.write(textstr)
	f.close()

def commandlineargs():
	# Allowing command line arguments to change key parameters in analysis

	# Initial values
	# Step size
	h = 0.01
	# Number of steps
	N = 20000
	# Number of steps taken before recording a data point
	rec_n = 100
	# Central galaxy free to move
	stationaryB = False
	# Intial Step is a RK4 step
	RK4step = True
	# Perturbing mass in parabolic orbit
	e = 1
	# Distance of closest approach
	f = 10
	# Initial angle of perturbing mass orbit
	i = 0.5
	# Initially antirotating wrt disturber
	co = False

	opts, args = getopt.getopt(sys.argv[1:],"sh:N:r:e:f:i:",["help","rk4off","co"])
	for opt, arg in opts:
		if opt == "--help":
			print("""
This program can take 8 different command line options:

-s (takes no argument):\t\tUsed to fix the central mass position
-h (takes float):\t\tChanges the step size used in the simulation
-N (takes int):\t\t\tChanges the number of steps taken
-r (takes int):\t\t\tChanges the number of steps taken before recording data
-e (takes float):\t\tChanges the eccentricity of the perturbing mass orbit
-f (takes float):\t\tChanges the distance of closest approach of the perturbing mass
-i (takes float):\t\tStarting angle of orbit, enter fraction of pi
--rk4off (takes no argument):\tInitial step is a Euler step
--co (takes no argument):\tSets tests masses to be corotating with distrubing orbit

""")
			sys.exit()
		elif opt == '-s':
			stationaryB = True
		elif opt == '-h':
			h = float(arg)
		elif opt == '-N':
			N = int(arg)
		elif opt == '-r':
			rec_n = int(arg)
		elif opt == '-e':
			e = float(arg)
		elif opt == '-f':
			f = float(arg)
		elif opt == '-i':
			i = float(arg)
		elif opt == '--rk4off':
			RK4step = False
		elif opt == '--co':
			co = True

	params = [h, N, int(N/rec_n), stationaryB, e, f, i, RK4step, co]
	paramstr = '\n\nStep size:\t\t\t{0}\nNumber of iterations:\t\t{1}\nNumber of data points:\t\t{2} \nFixed central mass:\t\t{3}\n\
Eccentricity:\t\t\t{4}\nClosest approach:\t\t{5}\nStarting angle:\t\t\t{6}\u03C0\nRK4 Step:\t\t\t{7}\nCorotating:\t\t\t{8}\n\n'.format(*params)
	print(paramstr)
	return h, N, rec_n, e, f, i, stationaryB, RK4step, co

def dubdig(t):
	# Returns a string which is 2 digits long for displaying times nicely
	if t < 10:
		t = '0'+str(t)
	else:
		t = str(t)
	return t

def sectotime(t):
	# Converts seconds to hours, minutes and seconds
	hrs = int(t / 3600)
	t -= 3600*hrs
	mins = int(t/60)
	t -= 60*mins
	time = [dubdig(hrs),dubdig(mins),dubdig(int(t))]
	return time

## Main ##

def main():
	# Ability to set h, N and rec_n via command line arguments as well as fixing the position of the central galaxy
	h, N, rec_n, e, f, iangle, fixed, RK4step, co = commandlineargs()

	# Records the intial wall time i.e. that measured by a stopwatch external to computer
	t0 = time.time()
	# Central stationary central mass
	R = np.zeros(2)
	V = np.array((0,0))
	stationaryG = Galaxy(1,R,V)

	# Moving mass
	R,V = orbit(f,e,iangle*np.pi)
	M = 1
	movingG = Galaxy(M,R,V)

	# Position and density of test particles
	radii = [2,3,4,5,6,7,8]
	densities = [12,18,24,30,36,42,48]

	# Creating test particles
	particles = stationaryG.createring(densities,radii,co)
	
	galaxy_masses = np.array((stationaryG.M,movingG.M))
	galaxy_postions = np.array((stationaryG.R,movingG.R))

	# Taking initial steps for both test particles and masses
	for x in particles:
		x.initialstep(h,galaxy_masses,galaxy_postions,RK4step)
	movingG.initialstep(h,stationaryG.M,stationaryG.R,RK4step)
	# Need to use stationaryG.Rold since the other galaxy has already been moved for this time step
	if not fixed:
		stationaryG.initialstep(h,movingG.M,movingG.Rold,RK4step)

	# Creating arrays to store position vector data
	record_testpositions = np.zeros((2,sum(densities),N/rec_n))
	record_galaxyposition = np.zeros((2,2,N/rec_n))

	# Main loop
	print("Performing simulation...\n")
	iteratort = 0

	for t in range(N):
		iteratorx = 0
		galaxy_postions = np.array((stationaryG.R,movingG.R))
		# Moving each test mass individually
		for x in particles:
			x.verletstep(h,galaxy_masses,galaxy_postions)
			if(t%rec_n == 0):
				particles_positions = x.returnvalues()
				record_testpositions[:,iteratorx,iteratort] = particles_positions
			iteratorx += 1
		# Stepping the two galaxies
		movingG.verletstep(h,stationaryG.M,stationaryG.R)
		# Need to use stationaryG.Rold since the other galaxy has already been moved for this time step
		if not fixed:
			stationaryG.verletstep(h,movingG.M,movingG.Rold)
		if(t%rec_n == 0):
			record_galaxyposition[:,0,iteratort] = stationaryG.R
			record_galaxyposition[:,1,iteratort] = movingG.R
			iteratort += 1

	# Finds the difference in wall times
	t_elapsed = time.time() - t0
	t_elapsed = sectotime(t_elapsed)
	timestr = "Runtime: "+t_elapsed[0]+" hrs "+t_elapsed[1]+" mins "+t_elapsed[2]+" secs"
	print('Completed simulation!\n',timestr,'\n\n\nPlotting...\n\n', sep = '')

	ps.plotdir()
	# Uncomment to plot delta r wrt time
	# plottr(h, len(radii), densities, record_testpositions, N, rec_n)
	plotpos(record_testpositions, record_galaxyposition, N, rec_n, f, e, fixed, t_elapsed, add_len = 30)

if __name__ == "__main__": main()
