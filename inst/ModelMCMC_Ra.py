#include <Rcpp.h>
#include <Python.h>
	#####################  Librerias
from numpy import isnan,savetxt,genfromtxt, array, log, unique, exp, append,concatenate,zeros, repeat,linspace
import pytwalk
#import cProfile
from scipy.stats import uniform
from numpy.random import seed



	#import csv
	##################### Read calibration curve

def plumMCMC(dirt,plomo,T_mod,num_sup,det_lim,iterations , by,shape1_m,mean_m,shape_acc,mean_acc,fi_mean,fi_acc,As_mean,As_acc,resolution,seeds):
	seed(int(seeds))
	#print(["direccion",dirt])
	#print(["fichero",plomo])
	#print(["modelo",T_mod])
	#print(["det limit",det_lim])
	#dirt,plomo,T_mod,num_sup,det_lim,iterations,burnin , by,shape1_m,mean_m,shape_acc,mean_acc = "/home/endymion/Documents/210Pb Python/Lead/TEST/","newset3.csv",False,	4   ,	.5 , int(.5e+2),int(.5e+2), 1.5,1.5,.7,1.5,10.
	fimean=fi_mean
	shapefi=fi_acc
	ASmaean=As_mean
	shapeAS=As_acc
	shape2_m= (shape1_m*(1-mean_m) )/mean_m
	scale_acc=mean_acc/shape_acc
	scale_fi=fimean/shapefi
	scale_As=ASmaean/shapeAS
	Data=genfromtxt (dirt+plomo, delimiter = ',')
	##################### Data definition 210Pb
	density=Data[:,1]   * 10.
	activity=Data[:,2]
	sd_act=Data[:,3]
	thic=Data[:,4]
	depth=Data[:,0]
	supp=Data[:,5]
	sd_supp=Data[:,6]
	Ran=len(supp)
	#print(Ran)

	#print((sum(supp)/len(supp)))

	activity=activity*density
	sd_act=sd_act*density

	lam=0.03114

	#depth=array(range(20))*1+1

	dep_time_data=append(depth-thic,depth)
	dep_time_data=list(set(dep_time_data))
	X1, X0= [],[]
	for i1 in range(len(depth)):
		for k1 in range(len(dep_time_data)):
			if depth[i1]== dep_time_data[k1]:
				X1=append(X1,int(k1))
			if (depth-thic)[i1]== dep_time_data[k1]:
				X0=append(X0,int(k1))
#	print(X0)
#	print(X1)
#	print(depth)
#	dep_time_data=dep_time_data
#	if dep_time_data[0] !=0.0:
#		dep_time_data=append(0,dep_time_data)
##	print(dep_time_data)
#	conti=array([])
#	for ci in range(len(depth)):
#		if ((depth-thic)-append(0,depth)[:len(depth)])[ci]!=0:
#				conti=append(conti,1)
#		else:
#			conti=append(conti,0)
	m=1
	breaks=array(m*by)
	while m*by< depth[-1]:
		m += 1
		breaks=append(breaks,m*by)


	#################### Functions

	def support(param):
		tmp3=True
		for i in param:
			if i <= 0.:
				tmp3=False
		if param[1+Ran]>=1.:
			tmp3=False
		if times([depth[-1]],param)[-1]>last_t(param[0]):
			tmp3=False
		return tmp3

	def last_t(fi):
		return(1./lam)*log(fi/det_lim)

	def ln_like_data(param):
		Asup=param[1:Ran+1]*density
		loglike = 0.
		tmp2=param[0]/lam
		ts=times(dep_time_data,param)
		for i in range(len(activity)):
			A_i= Asup[i] + tmp2 *(exp(-lam*ts[int(X0[i])] ) - exp(-lam*ts[int(X1[i])]) )#exp(tmp2 - lam*ts[int(X0[i])] ) - exp(tmp2 - lam*ts[int(X1[i])])
			Tau=.5*(sd_act[i]**(-2.))
			loglike = loglike + Tau*((A_i-activity[i])**2.)
		return loglike

	def ln_like_T(param):
		Asup=param[1:Ran+1]*density
		loglike = 0.
		tmp2=param[0]/lam
		ts=times(dep_time_data,param)
		for i in range(len(activity)):
			A_i= Asup[i] + tmp2 *(exp(-lam*ts[int(X0[i])] ) - exp(-lam*ts[int(X1[i])]) )#exp(tmp2 - lam*ts[int(X0[i])] ) - exp(tmp2 - lam*ts[int(X1[i])])
			Tau=.5*(sd_act[i]**(-2.))
			loglike = loglike + 3.5*log(4. + Tau*((A_i-activity[i])**2.) )
		return loglike


	def ln_like_supp(param):
		logsupp=0.
		for i in range(len(supp)):
			Tau=.5*(sd_supp[i]**-2.)
			logsupp = logsupp + Tau*((param[1+i]-supp[i])**2.)
		return logsupp

	def times(x,param):
		w=param[Ran+1]
		a=param[Ran+2:]
		t1=m-1
		ms1=array([a[m-1]])
		while t1 >0 :
		   ms1= append(ms1, w*ms1[-1]+(1-w)*a[t1-1])
		   t1 -= 1
		ms=ms1[::-1]
		ages=array([])
		y_last=append([0],array([sum(ms[:i+1]*by) for i in range(len(ms))] ) )
		for i in range(len(x)):
		   k1=0
		   while  breaks[k1]< x[i]:
			   k1 += 1
		   ages=append(ages,y_last[k1]+(ms[k1]*(by-(breaks[k1]-x[i]))))
		return ages

	def pendi(param):
		w=param[Ran+1]
		a=param[Ran+2:]
		t1=m-1
		ms1=array([a[m-1]])
		while t1 >0 :
		   ms1= append(ms1, w*ms1[-1]+(1-w)*a[t1-1])
		   t1 -= 1
		ms=ms1[::-1]
		return ms



	def ln_prior_supp(param):
		prior=0.
		prior= prior -  (  (shapefi-1.)*log(param[0])-(param[0]/scale_fi) )# prior for fi
		for k in range(Ran):
			prior= prior -  (  (shapeAS-1.)*log(param[1+k])-(param[1+k]/scale_As) )# prior for supp
		prior= prior -  ( ((1./by)-1.)*log(param[1+Ran])- log(by)+  ((1./by)*(shape1_m-1.))*log(param[1+Ran]) + (shape2_m - 1.)*log(1.-param[1+Ran]**(1./by) ) )# prior for w	#
		for ms in range(m):
		   prior= prior -  (  (shape_acc-1.)*log(param[ms+2+Ran])-(param[ms+2+Ran]/scale_acc) )
		return prior


	if T_mod:
		log_data=ln_like_T
	else:
		log_data=ln_like_data

	def obj(param):
		objval= ln_like_supp(param) + ln_prior_supp(param) + log_data(param)
		return objval




	#################### Initial valules
	print("Seaching initial values")
	fi_ini_1= uniform.rvs(size=1,loc=50, scale=200)  #200.
	fi_ini_2= uniform.rvs(size=1,loc=250, scale=150) #100.
	supp_ini_1= uniform.rvs(size=Ran,loc=15, scale=30) #5.
	supp_ini_2= uniform.rvs(size=Ran,loc=1, scale=15) #20.
	w_ini = uniform.rvs(size=1,loc=.2,scale=.3) #.3
	w_ini0 = uniform.rvs(size=1,loc=.3,scale=.3)  #.7
	m_ini_1=uniform.rvs(size=m,loc=0, scale=15)  #  repeat(array(3.1),m,axis=0)
	m_ini_2=uniform.rvs(size=m,loc=0, scale=15)  # repeat(array(.5),m,axis=0)
	#print("here")
	x=append(append(append(fi_ini_1,supp_ini_1),w_ini), m_ini_1)
	xp=append(append(append(fi_ini_2,supp_ini_2),w_ini0), m_ini_2)

	while not support(x):
	 	m_ini_1=uniform.rvs(size=m,loc=0, scale=3)
	 	x=append(append(append(fi_ini_1,supp_ini_1),w_ini), m_ini_1)


	while not support(xp):
	 	m_ini_2=uniform.rvs(size=m,loc=0, scale=3)
	 	xp=append(append(append(fi_ini_2,supp_ini_2),w_ini0), m_ini_2)

	print("initial values were obtained")


	################### MCMC
	################## New MCMC test
	print("Number of iterations,")
	print(iterations)
	thi = int((len(x)))*50 #100
	print("Thining,")
	print(thi)
	burnin=10000*len(xp) #20000
	print("Burnin,")
	print(burnin)
	print("Total iterations,")
	print(burnin + iterations*thi)


	leadchrono = pytwalk.pytwalk(n=len(x),U=obj,Supp=support)
	i, k ,k0, n=0 , 0, 0, len(x)
	U , Up = obj(x), obj(xp)
	por=int(iterations/10.)
	Output = zeros((iterations+1, n+1))
	Output[ 0, 0:n] = x.copy()
	Output[ 0, n] = U
	por2=int(burnin/5.)
	while i< iterations:
		onemove=leadchrono.onemove(x, U, xp, Up)
		k+= 1
		if (all([k<burnin,k % por2==0]) ):
			print("burn in progress")
			print int(100*(k+.0)/burnin)
		if (uniform.rvs() < onemove[3] ):
			x, xp, ke, A, U, Up =onemove
			k0+=1
			if all([k % thi ==0 , k>int(burnin)]):
				Output[i+1,0:n] = x.copy()
				Output[i+1,n] = U
				if any([i % por==0, i==0]) :
					print int(100*(i+.0)/iterations),"%"
				   #print((time.clock()-tiempomedir)/60)
				i+= 1
		else:
			if all([k % thi ==0 , k>int(burnin)]):
				Output[i+1,0:n] = x.copy()
				Output[i+1,n] = U
				if any([i % por==0, i==0]) :
					print int(100*(i+.0)/iterations),"%"
				   #print((time.clock()-tiempomedir)/60)
				i+= 1



	#Output=array(Output)
	print("Acceptance rate")
	print(k0/(i+.0))
	print("The twalk did", k, "iterations")


	##################
	"""
	out 0 -> Fi
	out 1 -> Supported Activity
	out 2 -> w
	out 3-n -> dates
	out -1 -> Energy
	"""
	savetxt(dirt+'Results/Results_output.csv', Output,delimiter=',')
	estim=[]
	for i in range((iterations-1)):
		estim.append(times(breaks,Output[(i+1),:-1])  )
	estim=array(estim)
	savetxt(dirt+'Results/dates.csv', estim  )
	intervals=[]

	for i in range(len(estim[1,])):
		sort=sorted(estim[:,(i)])
		mean=sum(sort)/len(sort)
		disc=int(len(sort)*.025)+1
		disc1=int(len(sort)*.975)
		sort=sort[disc:disc1]
		intervals.append([breaks[i],sort[0],mean,sort[-1]])

	savetxt(dirt+'Results/intervals.csv', intervals ,delimiter=',')
	depths=array([append([0.0],breaks)])
	savetxt(dirt+"Results/depths.csv", depths,delimiter=',')

	grafdepts=linspace(0,breaks[-1],resolution)
	grafdepts2=grafdepts+(grafdepts[1]-grafdepts[0])/2
	grafdepts2=grafdepts2[0:(len(grafdepts2)-1)]

	grafage=linspace(0,(max(estim[:,-1])+.10),resolution)
	y=[]
	for i in range(len(depths[0,:])-1):
		logvect=array(grafdepts2>depths[0,i])*array(grafdepts2<=depths[0,i+1])
		for k in range(len(logvect)):
			if logvect[k]:
				if i!=0:
					y1=estim[:,i-1]+((estim[:,i]-estim[:,i-1])/(depths[0,i+1]-depths[0,i]))*(grafdepts[k]-depths[0,i])
					porc=[]
					for posi in range(len(grafage)-1):
						porc.append(sum(array(y1>=grafage[posi])*array(y1<grafage[posi+1]) ))
					y.append(porc/(max(porc)+0.0 ))
				else:
					y1=((estim[:,i]/depths[0,i+1])*(grafdepts[k]) )
					porc=[]
					for posi in range(len(grafage)-1):
						porc.append(sum(array(y1>=grafage[posi])*array(y1<grafage[posi+1]) ))
					y.append(porc/(max(porc)+0.0 ))

	savetxt(dirt+"Results/Graphs.csv", array(y),delimiter=',')
	slopes=[]
	for i in range(iterations-1):
		slopes.append(pendi(Output[(i+1),:-1])  )
	savetxt(dirt+"Results/Slopes.csv", array(slopes),delimiter=',')






#D="/home/endymion/Documents/Joan -Caro/SAI2016/"
#plomo="SAI16Ra.csv"

#plumMCMC(D,plomo,False,.01,100,2.5,2.,.7,1.5,10)










