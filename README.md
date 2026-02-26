# C.D.M.P.
**C**onsulting  
**D**ata  
**M**anagment  
**P**latfrom  

## Overview

This Platfrom is meant to be used as a hub for keeping up and managing projects. 

<br>

<b>NOTE:</b> see last section on setting up environment variables (required for the file uploading to work)

## Installation
#### Create a Python Virtual Enviroment
You can create you virtual enviorment by running the following
```sh
python -m venv venv
```
After the script is done running

#### Activating the Virtual Enviorment
###### Windows
first you must allow scripts for the current user:
```sh
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
then you can activate the env
```sh
./venv/bin/activate.ps1
```
###### Unix/Linux
```sh
source ./venv/bin/activate
```
After that is done, you should see a *(venv)* indicator in front of input  

### Installing Required Libraries
When in Virtual Enviorment Run:
```sh
pip install -r requirements.txt
```

## Running the App
To run the flask app simply type in 
```sh
flask run
```
and this should open a live server on 
```sh
http://localhost:5000
```

## Environment Variables (REQUIRED)
- Create a file called `.env` at the root of the project (this file is in .gitignore, so it's not on the repo)
- Add the following content to `.env`
```
FILE_UPLOAD_STORAGE_PATH=c:/whatever/path/to/store/files
```
- (replace the value to match your api keys or paths on your system)