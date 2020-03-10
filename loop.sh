#!/bin/bash
while :
do
	rm Temp/*.png
	rm VideoStaging/*.png
	rm temp*
	python TwitterEngine.py
done