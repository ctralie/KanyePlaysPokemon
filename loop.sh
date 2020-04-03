#!/bin/bash
while :
do
    #Step 1: Open virtual screen buffer
    Xvfb :3 -screen 0 1024x768x24 &
    FrameBuf_PID=$!
    echo FrameBuffer PID: $FrameBuf_PID

    #Step 2: Remove temporary files from last time
	rm Temp/*.png
	rm VideoStaging/*.png
	rm temp*

    # Step 3: Run the engine
	DISPLAY=:3 python TwitterEngine.py

    # Step 4: Clean up processes
    pkill -f python
    pkill -f vba
    kill $FrameBuf_PID
    sleep 5
done