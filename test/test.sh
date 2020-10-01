#!/bin/sh -ex

wget -O inventory.xml "http://geofon.gfz-potsdam.de/fdsnws/station/1/query?net=GE&level=response"
fdsnxml2sacpz.py -T 2020-09-01T00:00:00Z -o sacpz-test- -v inventory.xml

