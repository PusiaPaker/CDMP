# C.D.M.P.
**C**onsulting  
**D**ata  
**M**anagment  
**P**latfrom  

## Overview

This Platfrom is meant to be used as a hub for keeping up and managing projects. 

<br>

## Start the App
### For Windows Systems:
```
python .\run_win.py
```
#### you will be prompted once for the file path on the first run. it should follow the format of: `C:\Users\YourName\wherever\somefolder`
#### if the file path is entered incorrectly, you can manually change it in the .env file after the run_win script is finished
### For Linux Systems:
- WIP
```

```

## Environment Variables (REQUIRED)
- Create a file called `.env` at the root of the project (this file is in .gitignore, so it's not on the repo)
- Add the following content to `.env`
```
FILE_UPLOAD_STORAGE_PATH=c:/whatever/path/to/store/files
```
- (replace the value to match your api keys or paths on your system)
