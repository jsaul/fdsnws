#!/usr/bin/env python

from __future__ import print_function

import sys, optparse, fnmatch
import fdsnws, fdsnws.paz

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
    from obspy.core import UTCDateTime
    opt.time = str(UTCDateTime(opt.time))

nslc_pattern = "%s.%s.%s.%s" % (opt.net, opt.sta, opt.loc, opt.cha)

if not arg:
    arg = [ sys.stdin ]

for xml_filename in arg:
    inventory = fdsnws.read_station_xml(xml_filename)
    pz_list = fdsnws.paz.inventory2sacpz(inventory, input_unit=opt.input_unit)

    for pz in pz_list:
        if not pz: # XXX FIXME
            continue
        if opt.verbose:
            print (fdsnws.paz.nslc(pz), nslc_pattern, file=sys.stderr)
        if not fnmatch.fnmatch(fdsnws.paz.nslc(pz), nslc_pattern):
            continue
            print ("matched", file=sys.stderr)
        if opt.time and not pz.start_date <= opt.time <= pz.end_date:
            continue

        if opt.prefix:
            fname = "%s%s_%s_%s" % (opt.prefix, fdsnws.paz.nslc(pz), pz["start_date"], pz["end_date"])
            ofile = open(fname, "w")
        else:
            ofile = sys.stdout
        ofile.write(pz.sacpz)
