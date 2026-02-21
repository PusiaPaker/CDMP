# C.D.M.P.
**C**onsulting  
**D**ata  
**M**anagment  
**P**latfrom  

## Overview

This Platfrom is meant to be used as a hub for keeping up and managing projects. 

<br>

<b>NOTE:</b> see last section on setting up environment variables (required for the file uploading to work)

## Start the App
#### For Windows Systems:
- 
```
python .\run_win.py
```
#### For Linux Systems:
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