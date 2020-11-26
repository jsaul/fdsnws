import sys
from obspy.core.inventory.response import PolesZerosResponseStage
from obspy.core import AttribDict

pz_header_template = """* **********************************
* NETWORK   (KNETWK): %(net)s
* STATION    (KSTNM): %(sta)s
* LOCATION   (KHOLE): %(loc)s
* CHANNEL   (KCMPNM): %(cha)s
* START             : %(start_date)s
* END               : %(end_date)s
* DESCRIPTION       : %(description)s
* LATITUDE          : %(lat).6f
* LONGITUDE         : %(lon).6f
* ELEVATION         : %(ele).1f
* DEPTH             : %(depth).1f
* DIP               : %(dip).1f
* AZIMUTH           : %(azimuth).1f
* SAMPLE RATE       : %(fsamp)g
* INPUT UNIT        : %(snj)s
* OUTPUT UNIT       : %(sno)s
* INSTTYPE          : %(sensor_type)s
* INSTGAIN          : %(sgn)g (%(inu)s)
* INSTGAIN FREQ     : %(sgf)g
* SENSITIVITY       : %(sensitivity_value)g (%(sni)s)
* SENSITIVITY FREQ  : %(sensitivity_frequency)g
* A0                : %(a0)g
* **********************************
"""

#* CREATED           : %(created)s

#if not opt.save_created:
#    del pz_header_template[5]
#pz_header_template = "\n".join(pz_header_template)


valid_units = { "M":0, "M/S":1, "M/S**2":2 }

def rectify_unit(unit):
    unit = unit.upper()
    # for accelerometers several unit strings have been
    # seen in the wild. We don't want to support them all.
    if unit in [ "M/S/S", "M/S^2" ]:
        unit = "M/S**2"
    try:
        assert unit in valid_units
    except:
        print(unit)
        raise
    return unit

def nslc(pz):
    return "%(net)s.%(sta)s.%(loc)s.%(cha)s" % pz


def obspy_nsc2sacpz(net, sta, cha, input_unit=None):
    """
    Convert an individual ObsPy inventory channel to a sacpz object
    """

    if input_unit is not None:
        input_unit = rectify_unit(input_unit)

    pz = AttribDict(
        net = net.code,
        sta = sta.code,
        loc = cha.location_code,
        cha = cha.code )


    pz.depth = cha.depth
    pz.start_date = str(cha.start_date)[:19]

#   if cha.end_date is not None:
#       if cha.end_date.timestamp > 1<<31:
#           cha.end_date = None
    if cha.end_date is not None:
        pz["end_date"] = str(cha.end_date)[:19]
    else:
        pz["end_date"] = "2599-12-31T23:59:59"
#   pz["created"] = str(inventory.created)[:19]


    pz.description = cha.description
    pz.dip = cha.dip
    pz.azimuth = cha.azimuth
    pz.fsamp = cha.sample_rate
    pz.lat = cha.latitude
    pz.lon = cha.longitude
    pz.ele = cha.elevation

    pz_stage = None
    for stage in cha.response.response_stages:
        if type(stage) == PolesZerosResponseStage:
            if not stage.pz_transfer_function_type.upper().startswith("LAPLACE"):
                continue
            if len(stage.poles)>0 or len(stage.zeros)>0:
#               if pz_stage is None:
                    pz_stage = stage
#               else:
#                   sys.stderr.write("%s: more than one PZ stage found - skipping this one\n" % nslc(pz))
    if not pz_stage:
        return
    pz.a0  = pz_stage.normalization_factor

    if not cha.sensor.manufacturer and not cha.sensor.model:
        # sloppy XML produced by the IRIS fdsnws
        pz.sensor_type = cha.sensor.type
    else:
        # properly populated XML
        pz.sensor_type = "%s %s" % (cha.sensor.manufacturer, cha.sensor.model)
    pz.sni = cha.response.instrument_sensitivity.input_units.upper()
    pz.sno = cha.response.instrument_sensitivity.output_units.upper()
    if not pz.sno or pz.sno == "None":
        sys.stderr.write("Warning: %s: setting empty OutputUnits to 'COUNTS'\n" % nslc(pz))
        pz.sno = "COUNTS"
    pz.sensitivity_value = cha.response.instrument_sensitivity.value
    pz.sensitivity_frequency = cha.response.instrument_sensitivity.frequency
    pz.sgn = pz_stage.stage_gain
    pz.sgf = pz_stage.stage_gain_frequency
    pz.inu = "%s / %s" % (pz_stage.output_units, pz_stage.input_units)
    if pz_stage.pz_transfer_function_type == "LAPLACE (RADIANS/SECOND)":
        factor = 1
    elif pz_stage.pz_transfer_function_type == "LAPLACE (HERTZ)":
        factor = 6.283185307179586
    else:
        raise TypeError("%s: unknown transfer function type '%s'" % (nslc(pz),pz_stage.pz_transfer_function_type))

    if input_unit is not None:
        if input_unit != pz_stage.input_units:
            dnz = valid_units[pz["sni"]]-valid_units[input_unit]
            if dnz == 0:
                pass # nothing to do
            elif 0 < dnz <=2:
                # add one or two zeros
                pz_stage.zeros.extend(dnz*[0.])
            else:
                raise NotImplementedError("removal of zeros not implemented")
        pz.snj = input_unit
    else:
        pz.snj = pz.sni

    zeros = []
    poles = []

    sacpz = "ZEROS   %d\n" % len(pz_stage.zeros)
    for zero in pz_stage.zeros:
        zero = complex(zero)*factor
        pz.a0 /= factor
        sacpz += "        %+.6e %+.6e\n" % (zero.real, zero.imag)
        zeros.append(zero)
    sacpz += "POLES   %d\n" % len(pz_stage.poles)
    for pole in pz_stage.poles:
        pole = complex(pole)*factor
        pz.a0 *= factor
        sacpz += "        %+.6e %+.6e\n" % (pole.real, pole.imag)
        poles.append(pole)
    sacpz += "CONSTANT %.6e\n" % (pz["a0"]*pz["sensitivity_value"])
    sacpz  = pz_header_template % pz + sacpz
    pz.sacpz = sacpz
    pz.poles = poles
    pz.zeros = zeros
    return pz


def inventory2sacpz(inventory, input_unit=None):
    """
    Convert a complete ObsPy inventory to a list of sacpz objects
    """

    pz_list = []

    for net in inventory:
        for sta in net:
            for cha in sta:
                pz = obspy_nsc2sacpz(net, sta, cha, input_unit)
                pz_list.append(pz)

    return pz_list

