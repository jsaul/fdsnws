#!/usr/bin/env python

from __future__ import print_function

import sys, optparse, fnmatch
import obspy.station.stationxml, obspy.station.response
import seis.paz.fdsn

description="%prog - convert FDSN Station XML to SAC Poles and Zeros"

p = optparse.OptionParser(usage="%prog [options] [files | < ] > ", description=description)

p.add_option("-N", "--net",          action="store", default="*", help="Network code")
p.add_option("-S", "--sta",          action="store", default="*", help="Station code")
p.add_option("-L", "--loc",          action="store", default="*", help="Location code")
p.add_option("-C", "--cha",          action="store", default="*", help="Channel code")
p.add_option("-T", "--time",         action="store",              help="Filter according to time")
p.add_option("-i", "--input-unit",   action="store",              help="M, M/S or M/S**2")
p.add_option("-o", "--prefix",       action="store",              help="write responses to separate files; filenames are formed using the specified prefix and station/channel codes etc.")
#p.add_option("-c", "--save-created", action="store_true",         help="Save creation time in comment header")
p.add_option("-v", "--verbose",      action="store_true",         help="run in verbose mode")


(opt, arg) = p.parse_args()
if opt.time:
    opt.time = str(obspy.core.UTCDateTime(opt.time))

nslc_pattern = "%s.%s.%s.%s" % (opt.net, opt.sta, opt.loc, opt.cha)

if not arg:
    arg = [ sys.stdin ]

for xml_filename in arg:
    obspy_inventory = obspy.station.stationxml.read_StationXML(xml_filename)
    pz_list = seis.paz.fdsn.inventory2sacpz(obspy_inventory, input_unit=opt.input_unit)

    for pz in pz_list:
        if opt.verbose:
            print (seis.paz.fdsn.nslc(pz), nslc_pattern)
        if not fnmatch.fnmatch(seis.paz.fdsn.nslc(pz), nslc_pattern):
            continue
            print ("matched")
        if opt.time and not pz["start_date"] <= opt.time <= pz["end_date"]:
            continue

        if opt.prefix:
            fname = "%s_%s_%s_%s" % (opt.prefix, seis.paz.fdsn.nslc(pz), pz["start_date"], pz["end_date"])
            ofile = file(fname, "w")
        else:
            ofile = sys.stdout
        ofile.write(pz["sacpz"])