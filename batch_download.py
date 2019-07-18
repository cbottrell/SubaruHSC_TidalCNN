#!/usr/bin/env python
import os
import sys
import time
import math
import tarfile
import shutil
from multiprocessing import Pool

import requests
from tqdm import tqdm

#===============================================================================
# This file will break the HSC-TF catalog into chunks and download them using
# the batch download feature from the HSC database. It will then extract and
# rename them, placing them in a dir called "images"
#
# There are a few things to be aware of:
# 1. update the creds dictionary in the download_file() function with your
#    username and password
# 2. If you want to only process part of the chunks change the start and end
#    variables in the main() function other wise you will process all ~106
#    chunks
# 3. The download is parallelized to 2 processes. I get 503 errors if I try to
#    to add another stream. The renaming will parallelize upto all available
#    processors so add an argument if you want to limit that
# 4. Downloading each file took about ~20 minutes on my desktop at the
#    university YMMV
# 5. The script expects the catalog to be in the same dir as the script, change
#    make_hsc_lists() if thats not the case

def download_file(args):
    submission = args

    creds = {
        "user":"your-username-here",
        "secret":"your-password-here"
    }

    with open(submission, "r") as f:
        while True:
            # https://stackoverflow.com/a/37573701
            r = requests.post("https://hsc-release.mtk.nao.ac.jp/das_cutout/pdr2/cgi-bin/cutout",
                                files={"list":f},
                                auth=(creds["user"], creds["secret"]),
                                stream=True)

            if r.status_code!=200:
                print(f"Failed Download for:{submission}. HTTP Code: {r.status_code}. Waiting 30 seconds...")
                time.sleep(30)
            else:
                break


    total_size = 1121597440  # approx from a download
    block_size = 1024
    wrote = 0
    with open(f'{submission}.tar.gz', 'wb') as f:
        for data in tqdm(r.iter_content(block_size),
                            total=math.ceil(total_size//block_size),
                            unit='KB', unit_scale=True,
                            desc=f"Downloading {submission}"):
            f.write(data)

def extract_and_rename(submission):
    new_dir = f"{submission}_dir"
    os.mkdir(new_dir)
    with tarfile.TarFile(f"{submission}.tar.gz", "r") as tarball:
        tarball.extractall(new_dir)

    with open(submission) as f:
        lines = [l.strip().split() for l in f.readlines()[1:]]

    out_dir = "images"
    if out_dir not in os.listdir():
        os.mkdir(out_dir)

    # the HSC api names the folder randomly
    sub_dir = os.listdir(new_dir)[0]

    img_dir = os.path.join(new_dir, sub_dir)
    completed = []
    for f in sorted(os.listdir(img_dir)):
        row_id = int(f.split("-")[0])

        obj_details = lines[row_id-2] # hsc counts from 1 and we dropped the header

        obj_id = obj_details[-1]
        band = obj_details[1].split("-")[1]

        os.rename(os.path.join(img_dir, f),
                  os.path.join(out_dir, f"{obj_id}_Cutout-525x525_{band}.fits"))
        completed.append(obj_details)

    for c in completed:
        lines.remove(c)

    shutil.rmtree(new_dir)

    if len(lines)>0:
        with open(f"{submission}.err.txt", "w") as f:
            f.write("The following objects failed:\n")
            for o in obj_details:
                f.write(",".join(o) + "\n")

# https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
def chunked(collection, chunk_size):
    for i in range(0, len(collection), chunk_size):
        yield collection[i:i+chunk_size]

def make_hsc_lists():
    # image size
    cutout_width = 525 # pixels
    arcsec_per_pixel = 0.168 # arcsec/pixel
    s_ang = cutout_width / 2 * arcsec_per_pixel # arcsec

    catalogue = "HSC-TF_all_2019-07-16.txt"
    filters = "GRIZY"

    # convert catalog to HSC acceptable lists and indices

    # docs: https://hsc-release.mtk.nao.ac.jp/das_cutout/pdr2/manual.html#list-to-upload
    # the list cannot be larger than 1000 images per request
    # so we can process 200 sources per request. The images
    # that are returned are identified by the line number
    # starting at 2
    with open(catalogue, "r") as f:
        objects = [l.strip().split(",") for l in f.readlines()[1:]]

    das_header = "#? rerun filter ra dec sw sh # column descriptor\n"
    das_submissions = []

    for i, obj_chunk in enumerate(chunked(objects, 2)):
        das_list = []
        for obj in obj_chunk:
            obj_id = obj[0]
            ra = obj[2]
            dec = obj[3]

            for filt in filters:
                row = f" pdr2_wide HSC-{filt} {ra} {dec} {s_ang}asec {s_ang}asec # {obj_id}"
                das_list.append(row)

        f_name = f"submit-{i}.txt"
        with open(f_name, "w") as f:
            f.write(das_header)
            f.write("\n".join(das_list))
        das_submissions.append(f_name)

        if i==2:
            break

def get_submissions(start, end):
    if start==0 and end==0:
        end = 106

    return [f"submit-{i}.txt" for i in range(start, end)]

def main():
    # change these based on how split up the data
    start = 0
    end = 0

    make_hsc_lists()

    das_submissions = get_submissions(start, end)

    # download
    with Pool(2) as p:
        p.map(download_file, das_submissions)
    # list(map(download_file, das_submissions))

    # extract and rename according to row index
    with Pool() as p:
        p.map(extract_and_rename, das_submissions)
    # list(map(extract_and_rename, das_submissions))

if __name__=="__main__":
    main()
