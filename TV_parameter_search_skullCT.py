"""
TV reconstruction example for simulated Skull CT data - lambda parameter search
"""
import odl
import numpy as np
import os
from adutils import *

# Discretization
discr_reco_space = get_discretization()

# Forward operator (in the form of a broadcast operator)
A = get_ray_trafo()

# Define fbp in order to use it as initial guess for TV reco
fbp = get_fbp(A)

# Data
rhs = get_data(A)

# Gradient operator
gradient = odl.Gradient(discr_reco_space, method='forward')

# Column vector of operators
op = odl.BroadcastOperator(A, gradient)

Anorm = odl.power_method_opnorm(A[1], maxiter=2)
Dnorm = odl.power_method_opnorm(gradient, 
                                xstart=odl.phantom.white_noise(gradient.domain), 
                                maxiter=10)

# Estimated operator norm, add 10 percent
op_norm = 1.1 * np.sqrt(len(A.operators)*(Anorm**2) + Dnorm**2)

print('Norm of the product space operator: {}'.format(op_norm))

lambs = (0.01, 0.005, 0.003, 0.001, 0.0008, 0.0005, 0.0003, 0.0001)

# Use FBP as initial guess
x_init = fbp(rhs)

for lamb in lambs:      
    # l2-squared data matching
    l2_norm = odl.solvers.L2NormSquared(A.range).translated(rhs)

    # Isotropic TV-regularization i.e. the l1-norm
    l1_norm = lamb * odl.solvers.L1Norm(gradient.range)

    # Combine functionals
    f = odl.solvers.SeparableSum(l2_norm, l1_norm)
    
    # Set g functional to zero
    g = odl.solvers.ZeroFunctional(op.domain)
    
    # Accelerataion parameter
    gamma=0.4
    
    # Step size for the proximal operator for the primal variable x
    tau = 1.0 / op_norm 
    	
    # Step size for the proximal operator for the dual variable y
    sigma = 1.0 / op_norm #1.0 / (op_norm ** 2 * tau)

    # Reconstruct
    callbackShowReco = (odl.solvers.CallbackPrintIteration() & #Print iterations
                odl.solvers.CallbackShow(coords=[None, 0, None]) & #Show parital reconstructions
                odl.solvers.CallbackShow(coords=[0, None, None]) & 
                odl.solvers.CallbackShow(coords=[None, None, 60]))
    	
    callbackPrintIter = odl.solvers.CallbackPrintIteration()
             
    # Use the FBP as initial guess
    x = x_init
    
    # Run such that every 5th iteration is saved (saveCont == 1) or only the last one (saveCont == 0)
    saveCont = 1
    savePath = '/lcrnas/data/Simulated/120kV/'
    
    if saveCont == 0:
        niter = 100
        odl.solvers.chambolle_pock_solver(x, f, g, op, tau=tau, sigma = sigma, 
                                          niter = niter, gamma=gamma, callback=callbackPrintIter)
        saveName = os.path.join(savePath,'reco/Reco_HelicalSkullCT_70100644Phantom_no_bed_Dose150mGy_TV_lambda{}_'.format(lamb) + 
                                          str(niter) + 'iterations.npy')
        np.save(saveName,np.asarray(x))
        
    else:    
        startiter = 5
        enditer = 101
        stepiter = 5
        niter = [int(i) for i in np.arange(startiter,enditer,stepiter)]
        saveNameStart = 'Reco_HelicalSkullCT_70100644Phantom_no_bed_Dose150mGy_TV_lambda{}_'.format(lamb)
        savePath = os.path.join(savePath,'reco',saveNameStart)
        for iterations in niter:
            odl.solvers.chambolle_pock_solver(x, f, g, op, tau=tau, sigma = sigma, 
                                              niter = stepiter, gamma=gamma, callback=callbackPrintIter)
            saveName = (savePath + '{}iterations'.format(iterations) + '.npy')
            np.save(saveName,np.asarray(x))
