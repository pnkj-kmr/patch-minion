#!/bin/sh


source $(pwd)/env/bin/activate

start()
{
$(pwd)/env/bin/python app.py -p8082
}
start

