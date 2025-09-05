@echo off
TITLE TTS Server

ECHO Starting the TTS Server...

REM Activate the virtual environment. The 'CALL' command is important.
CALL .\venv\Scripts\activate

ECHO Virtual environment activated. Starting server...
ECHO To stop the server, press CTRL+C in this window.
ECHO.

REM Run the Python server script
python server.py

ECHO Server has been stopped.
PAUSE