#!/usr/bin/env python

from astropy.io import fits
import numpy as np
import os,sys,glob
from rebin import rebin
from scipy import interpolate
import multiprocessing,time

# enviornment properties
SLURM_CPUS = int(os.environ['SLURM_JOB_CPUS_PER_NODE'])

# catalogue name
catName = '/home/bottrell/scratch/Subaru/HyperSuprime/Catalogues/HSC-TF_all_2019-07-16_size_estimates.txt'
catData = np.loadtxt(catName,delimiter=',',dtype='str')
# directory in which all of the downloaded HSC images are stored
idir = '/home/bottrell/scratch/Subaru/HyperSuprime/Data/Images/'
odir = '/home/bottrell/scratch/Subaru/HyperSuprime/Data/Resized/'

arcsec_per_pixel = 0.168
oShape = (512,512) # crop shape
rShape = (128,128) # rebin shape

objIDs = catData[:,0].astype(int)
ras = catData[:,2].astype(float)
decs = catData[:,3].astype(float)
# use r-band sizes to set scale
# sizes = catData[:,7].astype(float)/arcsec_per_pixel # pixels

filterIDs = ['g','r','i','z','y']
# filterIDs = ['i']
        
def Resize_Cutout(arg):
    fileName,outName,oShape,rShape = arg

    oRows,oCols = oShape[0],oShape[1]
    iData = fits.getdata(fileName)
    iShape = iData.shape
    # difference in rows and columns from desired shape
    dRows,dCols = iShape[0]-oRows,iShape[1]-oCols
    hRows,hCols = int(dRows/2),int(dCols/2)

    if dRows%2==0: # take equal number of rows from bottom and top
        oData = iData[hRows:-hRows,:]
    else: # take 1 more pixel from the top always
        oData = iData[hRows+1:-hRows,:]

    if dCols%2==0: # take equal number of rows from left and right
        oData = oData[:,hCols:-hCols]
    else: # take 1 more pixel from the left always
        oData = oData[:,hCols:-(hCols+1)]

    oShape = oData.shape
    oHdr = fits.getheader(fileName,1)
    # use rebin tool if new shape is smaller than input
    if rShape[0]<oShape[0]:
        oData = rebin(oData,rShape)*float(rShape[0]*rShape[1]/oShape[0]/oShape[1])
    # use interp2d if new shape is smaller than input
    if rShape[0]>oShape[0]:
        x = np.linspace(0,1,oShape[0])
        y = np.linspace(0,1,oShape[1])
        f = interpolate.interp2d(x, y, oData, kind='linear')
        xn = np.linspace(0,1,rShape[0])
        yn = np.linspace(0,1,rShape[1])
        oData = f(xn,yn)
    oHdr['NAXIS1']=rShape[1]
    oHdr['NAXIS2']=rShape[0]
    fits.writeto(outName,data=oData,header=oHdr)

# list of filenames, output names, crop shapes and final shapes
args = [ ('{}{}_Cutout-525x525_{}.fits'.format(idir,objID,filterID),'{}{}_Cutout-Resized_{}.fits'.format(odir,objID,filterID),oShape,rShape) for objID,ra,dec in zip(objIDs,ras,decs) for filterID in filterIDs ]

argList = []
for arg in args:
    if os.access(arg[0],0) and not os.access(arg[1],0):
        argList.append(arg)
argList = list(set(argList))

if __name__ == '__main__':
    pool = multiprocessing.Pool(SLURM_CPUS)
    pool.map_async(Resize_Cutout, argList)
    pool.close()
    pool.join()
