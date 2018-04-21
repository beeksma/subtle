# Welcome to Subtle
<p align="center">
<img src="https://user-images.githubusercontent.com/1226128/39083582-159431a6-455e-11e8-86c6-3da36a564d6e.png" alt="Subtle">
</p>


**Subtle is a light-weight subtitle downloader with multi-language support, written in Python and utilising the [OpenSubtitles.org API](http://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC)**. It runs as a service and provides an intuitive way to pick the video file you need subtitles for. Once you select a subtitle from the results returned by OpenSubtiles, this subtitle is automatically downloaded to the location of the selected video file. It's renamed to match the file name of the video, so you can start using it in your favourite video player right away.

## Screenshots

<p align="center">
<img src="https://user-images.githubusercontent.com/1226128/39084520-3b7e2244-456f-11e8-8e35-d22ebf6a33da.png" alt="The landing page">
<img src="https://user-images.githubusercontent.com/1226128/39084523-519c613a-456f-11e8-9684-b16cd5b72d14.png" alt="Navigate your video folders">
<img src="https://user-images.githubusercontent.com/1226128/39084533-73c87fbe-456f-11e8-88ff-fbfa53463ca0.png" alt="Select a subtitle to download">
</p>

## Requirements
 
 - A Linux installation (but should work on Windows as well) with write-access to the directories containing your video files
 - Python 3.5.4 + some dependencies
 - A (free) account on [OpenSubtitles.org](https://www.opensubtitles.org)
 
## Installation (Debian/Ubuntu)

Install Python, Pip and Git.

    sudo apt install -y python3 python3-pip git

Create a folder for Subtle in the 'opt' folder and change ownership of the folder to your username and group (e.g. 'ubuntu'). Next, clone this repo.

    cd /opt
    sudo mkdir subtle
    sudo chown ubuntu:ubuntu subtle
    git clone https://github.com/beeksma/subtle.git

Open the Subtle directory and use pip to install the Python modules required by Subtle.

    cd subtle
    sudo pip3 install -r requirements.txt 

Copy *config.json.sample* to *config.json* and open the new file in your favourite text editor (e.g. nano).

    cp config.json.sample config.json
    nano config.json

Update the configuration file with your OpenSubtitles username and password. For security purposes, your password will be hashed the first time Subtle runs. You should also update the 'root' value with the path to your video files. If you leave this blank, the root folder of your system (e.g. '/') will be used instead.

    {
    "os_username": "myusername",
    "os_password": "password123",
    "hash": "",
    "root": "/path/to/my/video_files",
    "debug" : "no"
    }

By default, Subtle will search for subtitles in the English language. In order to download subtitles in your preferred language, go to OpenSubtitles.org, log in with the credentials you used above, and open your profile page. Select your preferred languages and click 'Commit changes' at the bottom of the list.

Next, ensure 'Subtle' is an executable and run it to start Subtle in daemon mode.

    chmod +x Subtle
    ./Subtle

**Subtle now listens on port 8979 and can be accessed in your browser via http://127.0.0.1:8979/subtle.** If you're not running Subtle on your local machine, replace '127.0.0.1' with the correct IP address. Optionally you can [set up a reverse proxy](https://duckduckgo.com/?q=how+to+set+up+a+reverse+proxy&t=ffab&ia=web) in order to use your domain name instead.

## Start Subtle automatically on boot using systemd

First, copy the init script in the *systemd* folder to */etc/systemd/system* and edit it in your favourite text editor (e.g. nano)

    cd /opt/subtle/systemd
    sudo cp subtle-subs.service /etc/systemd/system
    sudo nano /etc/systemd/system/subtle-subs.service 

Update the user and group to match the desired user on your server. **Please note that the user should have write-access to the folders containing your video files, as it won't be able to save your subtitles otherwise!**

    [Unit]
    Description=Subtle instance (Gunicorn)
    After=network.target
    
    [Service]
    User=ubuntu <-- change this to match your system
    Group=ubuntu <-- this one too
    PIDFile=/run/gunicorn/pid
    RuntimeDirectory=gunicorn
    WorkingDirectory=/opt/Subtle
    ExecStart=/usr/local/bin/gunicorn --pid subtle.pid   \
              -b 0.0.0.0:8979 Subtle:app
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    PrivateTmp=true
    
    [Install]
    WantedBy=multi-user.target

Enable the init script. Then make sure Subtle isn't already running (if it is, either use *htop* to kill it or restart your computer) and start the service.

    sudo systemctl enable subtle-subs.service
    sudo systemctl start subtle-subs.service

## License

* [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)
* Copyright 2017 - 2018

## Powered by

 - [OpenSubtitles.org](https://www.opensubtitles.org)
 - [Flask](http://flask.pocoo.org/)
 - [Bootstrap](https://getbootstrap.com/)

## Finally

Please note that this software comes without any warranty or support, use it at your own risk. If you run into any problems raise an issue here on GitHub and I'll try to help out.

Hope you like Subtle :)