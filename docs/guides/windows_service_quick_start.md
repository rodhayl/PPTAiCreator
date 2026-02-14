# Quick Start Guide - Service Management

## Overview

Two simple batch scripts manage the PPTAgent Streamlit service:

| Script | Purpose | How to Use |
|--------|---------|-----------|
| `start.bat` | Start the Streamlit service | Double-click to start |
| `stop.bat` | Stop the Streamlit service | Double-click to stop |

## Smart Detection

Both scripts automatically detect if the service is running, **regardless of how it was started**:
- ✅ Detects if already running (won't start twice)
- ✅ Detects if already stopped (won't fail)
- ✅ Works even if service was started manually or in background
- ✅ Works across system restarts (always finds running instance)
- ✅ Robust PID extraction and process termination
- ✅ Fallback process killing methods
- ✅ Waits for service to fully initialize

## Usage Examples

### Starting the Service

1. Navigate to the PPTAgent root directory
2. Double-click `start.bat`
3. Wait 2-3 seconds for startup
4. Access at: http://localhost:8501

**What happens:**
- Checks if port 8501 is already in use
- If running: Reports that service is already active
- If not running: Starts Streamlit in background
- Displays the access URL

### Stopping the Service

1. Navigate to the PPTAgent root directory
2. Double-click `stop.bat`
3. Service stops immediately

**What happens:**
- Checks if port 8501 is in use
- If running: Finds the process ID and terminates it
- If not running: Reports that service is already stopped
- Verifies the port is released

## Key Features

### Persistent Detection
The scripts use port monitoring, not process tracking:
- Works even if the console window was closed
- Works even if started from a different location
- Works even if started by another user
- Works across system reboots

### Error Handling
Gracefully handles various scenarios:
- Already running → Informs user and exits cleanly
- Already stopped → Informs user and exits cleanly
- Directory check → Verifies it's run from correct location
- Port verification → Confirms successful start/stop

### Background Execution
`start.bat` uses a VBScript launcher:
- Starts Streamlit without opening console window
- Service runs in background
- Computer remains responsive
- You can close the command window after starting

## Network Access

### Local Access (Same Machine)
```
http://localhost:8501
```

### Remote Access (Other Machines)
```
http://<YOUR_COMPUTER_IP>:8501
```

To find your IP address:
```bash
ipconfig
```
Look for "IPv4 Address" (usually starts with 192.168 or 10.x.x.x)

## Troubleshooting

### Scripts won't run
- Make sure you're in the PPTAgent root directory
- Check that Python is installed: `python --version`
- Check Streamlit: `pip install streamlit`

### Service won't start
- Port 8501 might be in use by another application
- Check: `netstat -ano | findstr :8501`
- Try `stop.bat` first, then `start.bat`

### Service won't stop
- Try running `stop.bat` as Administrator
- Use Task Manager to manually kill python.exe
- Wait 30 seconds for port to release

### Service started but can't access
- Try http://localhost:8501 (not 127.0.0.1)
- Check firewall isn't blocking port 8501
- Ensure Streamlit is fully initialized (wait 5-10 seconds)

## Technical Details

### What the Scripts Do

**start.bat:**
```
1. Check if port 8501 is in use
2. If yes → Tell user it's already running
3. If no → Validate directory (src/app.py exists)
4. Create temporary VBScript launcher
5. Execute launcher in background (no console)
6. Wait 2 seconds for startup
7. Verify service is listening on port 8501
8. Display success/failure message
9. Clean up temporary launcher script
```

**stop.bat:**
```
1. Check if port 8501 is in use
2. If no → Tell user it's not running
3. If yes → Extract process ID (PID)
4. Terminate process with taskkill /F
5. Wait 1 second for cleanup
6. Verify port is no longer in use
7. Display success/failure message
```

### Port Monitoring Command
Both scripts use this to check service status:
```
netstat -ano | findstr :8501
```

- `netstat -ano` → Show all network connections with PIDs
- `findstr :8501` → Filter for port 8501 only
- `errorlevel 0` → Port found (service running)
- `errorlevel non-zero` → Port not found (service stopped)

## Automation Ideas

### Create Desktop Shortcut
1. Right-click `start.bat` → Send to → Desktop (create shortcut)
2. Repeat for `stop.bat`
3. Pin shortcuts to taskbar or Start menu
4. Click for instant access

### Create Windows Scheduled Task
Run service automatically at startup:
```
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start program (start.bat)
5. Options: Run with highest privileges
6. Repeat: Don't set to stop automatically
```

### Create Batch Macro
Create a single script that toggles service:
```batch
@echo off
netstat -ano | findstr :8501 > nul
if %errorlevel% equ 0 (
    call stop.bat
) else (
    call start.bat
)
```

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `start.bat` | ~80 lines | Start service with smart detection |
| `stop.bat` | ~75 lines | Stop service with smart detection |
| `SERVICE_MANAGEMENT.md` | ~300 lines | Detailed documentation |
| `QUICK_START.md` | This file | Quick reference guide |

## Support

For detailed documentation, see: `SERVICE_MANAGEMENT.md`

For issues or questions:
1. Check the troubleshooting section above
2. Review SERVICE_MANAGEMENT.md for detailed info
3. Check that Python and Streamlit are properly installed
4. Verify no firewall is blocking port 8501

---

**Version:** 1.0
**Last Updated:** 2025-11-05
**Requirements:** Windows XP SP3+, Python 3.7+, Streamlit
