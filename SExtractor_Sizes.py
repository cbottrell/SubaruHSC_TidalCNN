#!/usr/bin/env python

# Compute SExtractor sizes and create new catalogue

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import os,sys,datetime,time
from glob import glob
from astropy.io import fits
from astropy.wcs import WCS
import sep
now = datetime.datetime.now()
author = 'Connor Bottrell'

def Generate_Segmap(filename,galaxy_coordinates_wcs):
    '''
    Return a segmentation map where: (1) only the target galaxy is 
    included in the map and everything else is background; and (2)
    every object has a unique flag and the target is at the center
    of the colormap. Next returns are (3) the flagID of the 
    primary galaxy, (4) median background estimate (sky only),
    (5) rms estimate of background (sky pixels), (6) a catalog of
    all object properties.
    '''
    # Primary HDU for file
    hdulist = fits.open(filename)
    # obtain wcs info
    w = WCS(hdulist[1].header, hdulist)
    # image data
    image = hdulist[1].data.astype(float)
    # close Primary HDU
    hdulist.close()
    # filter kernel
    filter_kernel = np.loadtxt('/home/bottrell/utils/sdss-cfg/gauss_3.0_7x7.conv',skiprows=2)
    # use std of full image as detection threshold
    guess_rms = np.std(image)
    # mask all sources above std for background statistics
    mask = (image>guess_rms)
    # bkg object which includes sky() and rms() methods
    bkg = sep.Background(image, mask=mask, bw=32, bh=32, fw=3, fh=3)
    # run sep.extract() on image
    objCat,sexseg = sep.extract(image, thresh=1.0, err=bkg.rms(), mask=None, minarea=5,
                             filter_kernel=filter_kernel,filter_type='conv',deblend_nthresh=32,
                             deblend_cont=0.001, clean=True,clean_param=1.0, segmentation_map=True)
    # median background
    bkg_med = np.median(image[sexseg==0])
    # background noise
    bkg_rms = np.std(image[sexseg==0])
    # determine galaxy position in pixels (origin 0 for python indexing)
    galaxy_coordinates_pixels = tuple(w.wcs_world2pix([galaxy_coordinates_wcs],0).astype(int)[0][::-1])
    # identify flag for target galaxy in segmentation map
    pflag = sexseg[galaxy_coordinates_pixels]
    # galaxy segmentation map (only these pixels are used in the model)
    galseg = sexseg==pflag
    return galseg,sexseg,pflag,bkg_med,bkg_rms,objCat

catName = '/home/bottrell/scratch/Subaru/HyperSuprime/Catalogues/HSC-TF_all_2019-07-16_size_estimates.txt'
catData = np.loadtxt(catName,delimiter=',',dtype='str')

# objIDs = catData[:,0].astype(int)
# ras = catData[:,2].astype(float)
# decs = catData[:,3].astype(float)

# Subaru HSC pixel scale
arcsec_per_pixel = 0.168

# priority ordering of filterIDs
filterIDs = ['g','r','i','z','y']

with open(catName,'r') as f:
    lines = f.readlines()
    
newCat = '/home/bottrell/scratch/Subaru/HyperSuprime/Catalogues/HSC-TF_all_2019-07-25.txt'

# if os.access(newCat,0):os.remove(newCat) #!!! Remove after testing
    
if not os.access(newCat,0):
    with open(newCat,'w') as f:
        f.write('#'*50+'\n')
        f.write('# File initialized: {}\n'.format(datetime.datetime.now()))
        f.write('# By: {}\n'.format(author))
        f.write('#'*50+'\n')
        header = lines[0].split('\n')[0].split(',')
        header = header + ['req_sex_{}'.format(filterID) for filterID in filterIDs]
        header[0] = 'objectID_Cat'
        for ii,entry in enumerate(header):
            f.write('# [{}] {}\n'.format(ii,entry))
        f.write('#'*50+'\n')
    objIDs_Done = np.array([])
else:
    objIDs_Done = np.loadtxt(newCat,delimiter=',',dtype='str')[:,0].astype(int)


imgDir = '/home/bottrell/scratch/Subaru/HyperSuprime/Data/Images/'

for line in lines[1:]:

    line = line.split('\n')[0]
    objID,z,ra,dec=line.split(',')[:4]
    objID = int(objID)
    if objID in objIDs_Done: continue
    z = float(z)
    ra = float(ra)
    dec = float(dec)
    
    req_arcsec = np.zeros(len(filterIDs))
    
    for i,filterID in enumerate(filterIDs):
        # filename
        fileName = '{}{}_Cutout-525x525_{}.fits'.format(imgDir,objID,filterID)
        # continue if image does not exist
        if not os.access(fileName,0):
            req_arcsec[i] = -1
            continue
        galaxy_coordinates_wcs = (ra,dec)

        try:
            galseg,sexseg,pflag,bkg_med,bkg_rms,objCat = Generate_Segmap(fileName,galaxy_coordinates_wcs)
            area_pixels = objCat[pflag-1][1]
            req_pixel = np.sqrt(float(area_pixels)/np.pi)
            req_arcsec[i] = req_pixel*arcsec_per_pixel
        except:
            req_arcsec[i] = -999

    newLine = ','.join(['%0.3f'%req_arcsec[i] for i in range(len(filterIDs))])
    with open(newCat,'a') as f:
        f.write('{},{}\n'.format(line,newLine))