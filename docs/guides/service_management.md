# PPTAgent Service Management

This document explains how to use the `start.bat` and `stop.bat` scripts to manage the Streamlit service.

## Quick Start

### Starting the Service

Double-click `start.bat` to start the Streamlit application:

```batch
start.bat
```

The script will:
1. ✅ Check if the service is already running on port 8501
2. ✅ Start the service if it's not running
3. ✅ Notify you if it's already running
4. ✅ Display the access URL (http://localhost:8501)

### Stopping the Service

Double-click `stop.bat` to stop the Streamlit application:

```batch
stop.bat
```

The script will:
1. ✅ Check if the service is running on port 8501
2. ✅ Stop the service if it's running
3. ✅ Notify you if it's already stopped
4. ✅ Verify the port is released

## Features

### Smart Detection
Both scripts intelligently detect if the service is running, **regardless of how it was started**:
- ✅ Detects services started with `start.bat`
- ✅ Detects services started manually from command line
- ✅ Detects services started from other applications
- ✅ Detects services started in the background
- ✅ Works even if the service wasn't started with these scripts

### Port Monitoring
The scripts monitor port 8501 using `netstat`, which is the standard Streamlit port:
- Uses Windows built-in `netstat` command (no external tools needed)
- Accurately identifies which process is using the port
- Safely kills only the intended process

### Error Handling
Comprehensive error handling includes:
- ✅ Checks if running in correct directory
- ✅ Validates Python installation
- ✅ Checks for port conflicts
- ✅ Graceful handling of already-running/stopped services

## Requirements

- Windows operating system (XP SP3 or later)
- Python installed and in PATH
- Streamlit installed (`pip install streamlit`)
- Run from the PPTAgent root directory

## Troubleshooting

### Service won't start
1. Make sure you're in the PPTAgent root directory
2. Check that Python is installed: `python --version`
3. Check that Streamlit is installed: `pip install streamlit`
4. Verify port 8501 is not in use by another application

### Service won't stop
1. Try running `stop.bat` as Administrator
2. Check Task Manager for hanging python.exe processes
3. Manually kill the process: `taskkill /IM python.exe /F`

### Port 8501 still in use after stopping
- Windows sometimes takes a moment to release the port
- Try running `stop.bat` again or waiting 30 seconds
- Use `netstat -ano | findstr :8501` to check the port status

## Manual Control

If the batch scripts don't work, you can manage the service manually:

### Start manually
```bash
python -m streamlit run src/app.py --server.port=8501
```

### Find the process
```bash
netstat -ano | findstr :8501
```

### Stop manually
Replace `PID` with the actual process ID from netstat:
```bash
taskkill /PID PID /F
```

## Script Details

### start.bat
- Checks port 8501 using `netstat`
- Uses VBScript launcher to run Streamlit in background without console window
- Waits 2 seconds and verifies the service started
- Displays friendly status messages

### stop.bat
- Checks port 8501 using `netstat`
- Extracts the process ID (PID) using text parsing
- Terminates the process using `taskkill /F`
- Verifies the port is released

## Automation

You can create shortcuts to these scripts for easier access:

1. Right-click on `start.bat` → Create shortcut
2. Right-click on the shortcut → Properties
3. Change "Start in" to the PPTAgent directory
4. Optionally change the icon and name
5. Pin to Start menu or desktop for quick access

## Environment Variables

The scripts don't require any environment variables, but if you need to customize the port:

Edit `start.bat` and change this line:
```batch
objShell.Run "python -m streamlit run src/app.py --server.port=8501", 0, False
```

Change `8501` to your desired port, then update `stop.bat` accordingly.

## Service Access

Once running, access the application at:
```
http://localhost:8501
```

You can also access it from other machines on your network:
```
http://<YOUR_IP_ADDRESS>:8501
```

## Performance Notes

- Initial startup takes 10-15 seconds as Streamlit initializes
- Subsequent runs are faster (2-5 seconds)
- Service runs in background; minimize the command window
- Service will continue running even if you close the command window

---

**Last Updated:** 2025-11-05
**Version:** 1.0
