#!/bin/bash
while [ 1 ] #Infinite loop
do
	date
	timeout 100 python `dirname $0`/predictor.py checkprice
	#100 seconds timeout to kill script if cryptsy being shitty
	sleep 120 #2 mins between runs
done