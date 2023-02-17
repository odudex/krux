# Running Krux on your PC Through Kivy
This was the steps to run and build Krux APK on a fresh Ubuntu environment

## Install Kivy
Requirements
```
sudo apt-get install -y \
    python3-pip \
    build-essential \
    git \
    python3 \
    python3-dev \
```
Kivy Repo
```
sudo add-apt-repository ppa:kivy-team/kivy
```

```
sudo apt-get update
```
Install Kivy
```
sudo apt-get install python3-kivy
```

## Install Krux python dependencies

```
sudo apt install python3-zbar embit
```


```
pip3 install embit pyqrcode pyzbar gestures4kivy camera4kivy
```

## Run the app on your computer

Enter the /android folder run:

```
python3 main.py
```
Try to shape the window close to a phone aspect and be aware the font may be too big for a computer screen.

After successfully running the app through Kivy on desktop, let's install buildozer to build the apk

# Build the APK with Buildozer

## Install Buildozer
```
pip3 install --user --upgrade buildozer
```

## Install Buildozer dependencies
```
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev gettext
```

```
pip3 install --user --upgrade Cython==0.29.19 virtualenv
```

Add the following line at the end of your ~/.bashrc file

```
export PATH=$PATH:~/.local/bin/
```

## Build the app
```
buildozer android debug
```
First time will take a LONG time because it will download and install Android SDK.

When ready, you can find the apk on the 'bin' folder

Put your phone in developer mode, connect it with an USB cable an deploy the app:
```
buildozer android deploy run
```

# Todo:

As you may have noticed, Krux `/src` folder is duplicaded (with a few modifications) inside android folder. I'm still looking for an ideal solution to build the app from the main `/src` folder

