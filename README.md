# SubaruHSC tidal feature characterization with CNN

Group repo for the tidal CNN project. 

## Instructions for getting images:

### Unagi

Make sure you are using a python environment that you are comfortable changing. Always good practice to make a new virtual environment or conda environment for a new project. If it requires activation, `activate` it.

I use Song Huang’s `unagi` package — which you will have to clone from its git repository:

    git clone https://github.com/dr-guangtou/unagi.git

You must then go into the `unagi` directory and do:

    python setup.py install
    
This will put an `unagi` egg in the `site-packages` directory of your python module library located at `path_to_my_env/lib/pythonX.X/site-packages`. You can check the installation by moving to a directory that does not contain the `unagi` directory and starting python:

    import unagi

If that does not throw an error, your installation is stable. 

### Environment variables

In order to download images, you must have a Subaru account: https://hsc-release.mtk.nao.ac.jp/datasearch/new_user/new

You will select a username and be given a (long) password. Once you have a username and password, add them as environment variables to your `.bash_profile` or `.bashrc` or `.profile`. Alternatively, you can also add them to the `activate` file for your python environment. These steps prevent you from being asked for your username and password for every download.

In bash:

    export SSP_PDR_USR='xxx'
    export SSP_PDR_PWD='yyy'
    
### Downloading images

I have written a short script, `GetHSC_Cutouts.py`, for downloading the images. Modify it however you like on your branch. It currently grabs images in all `grizy` bands, making cutouts roughly 525x525 in size. I picked this size because the WCS matrices are not the same for every location accross the survey... Meaning that some images will be 524x526, etc. I can trim all of these down to 512x512 in post-processing, then resample to lower resolution or cutout a specified region.

Go into the `GetHSC_Cutouts.py` file and change the path to the Catalogues and your desired output directory (which I have confusingly called `Input` in my folder since I consider it as input for CNNs. You will then be ready to download images. Message me on slack if you have an issue.
