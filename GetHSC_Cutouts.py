#!/usr/bin/env python
import os,sys,time
import numpy as np
import astropy.units as u
from astropy import wcs
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.utils.data import download_file, clear_download_cache
from unagi import config
from unagi import hsc
from unagi import plotting
from unagi.task import hsc_cutout

pdr2 = hsc.Hsc(dr='pdr2', rerun='pdr2_wide')

cutout_width = 525 # pixels
arcsec_per_pixel = 0.168 # arcsec/pixel
s_ang = cutout_width / 2 * arcsec_per_pixel * u.arcsec # arcsec

# Catalogue
catalogue = '/Users/cbottrell/Project/HSC-Subaru/Catalogues/HSC-TF_all_2019-07-16.txt'
output_dir = '/Volumes/Project_Data/HSC_Subaru/Input/' 
# filename prefix
prefix = '{}_Cutout-{}x{}'

cat_data = np.loadtxt(catalogue,delimiter=',',dtype='str')
objIDs = cat_data[:,0].astype(int)
ras = cat_data[:,2].astype(float)
decs = cat_data[:,3].astype(float)
zs = cat_data[:,1].astype(float)

filterIDs = ['g','r','i','z','y']

for objID,ra,dec,z in zip(objIDs,ras,decs,zs):
    
    # check if y-band image exists (last in list), if true, continue
    fileLast = output_dir+prefix.format(objID,cutout_width,cutout_width)+'_{}.fits'.format(filterIDs[-1])
    if os.access(fileLast,0): continue
    else: print(objID)    
    # start with no filters
    filters = ''

    # only make images in filters for which images do not already exist
    for filterID in filterIDs:
        fileName = output_dir+prefix.format(objID,cutout_width,cutout_width)+'_{}.fits'.format(filterID)
        if not os.access(fileName,0): filters+=filterID
        
    # coordinate generator
    coord = SkyCoord(ra, dec, frame='icrs', unit='deg')
    
    # make cutouts
    try:
    
        try:
            cutout_multi = hsc_cutout(coord, cutout_size=s_ang, filters=filters, archive=pdr2,
                                    use_saved=False, output_dir=output_dir, variance=0, mask=0,
                                    prefix=prefix.format(objID,cutout_width,cutout_width))
        
        # sleep a bit if this doesn't work, and retry
        except:
            time.sleep(120)
            cutout_multi = hsc_cutout(coord, cutout_size=s_ang, filters=filters, archive=pdr2,
                                      use_saved=False, output_dir=output_dir, variance=0, mask=0,
                                      prefix=prefix.format(objID,cutout_width,cutout_width))
    except:
        continue
