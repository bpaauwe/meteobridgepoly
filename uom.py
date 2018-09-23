# Unit of Measure map
#
# Map the editor ID to the ISY UOM number

UOM = {
        'TEMP_C': 4,
        'TEMP_F': 17,
        'I_HUMIDITY': 51,
        'I_MB': 117,
        'I_INHG': 23,
        'I_TREND': 25,
        'I_KPH': 32,
        'I_MPH': 48,
        'I_DEGREE': 14,
        'I_MMHR': 46,
        'I_INHR': 24,
        'I_MM': 82,
        'I_INCH': 105,
        'I_UV': 71,
        'I_LUX': 36,
        'I_RADIATION': 74,
        'I_STRIKES': 56,
        'I_KM': 83,
        'I_MILE': 116,
        'I_MPS' : 49,
        }


TEMP_DRVS = {
        'main' : 'ST',
        'dewpoint' : 'GV0',
        'windchill' : 'GV1',
        'heatindex' : 'GV2',
        'apparent' : 'GV3',
        'inside' : 'GV4',
        'extra1' : 'GV5',
        'extra2' : 'GV6',
        'extra3' : 'GV7',
        'extra4' : 'GV8',
        'extra5' : 'GV9',
        'extra6' : 'GV10',
        'extra7' : 'GV11',
        'extra8' : 'GV12',
        'extra9' : 'GV13',
        'extra10' : 'GV14',
        'max' : 'GV15',
        'min' : 'GV16',
        'soil' : 'GV17',
        }

HUMD_DRVS = {
        'main' : 'ST',
        'inside' : 'GV0',
        'extra1' : 'GV1',
        'extra2' : 'GV2',
        'extra3' : 'GV3',
        'extra4' : 'GV4',
        'extra5' : 'GV5',
        }

PRES_DRVS = {
        'station' : 'ST',
        'sealevel' : 'GV0',
        'trend' : 'GV1'
        }

WIND_DRVS = {
        'windspeed' : 'ST',
        'winddir' : 'GV0',
        'gustspeed' : 'GV1',
        'gustdir' : 'GV2',
        'lullspeed' : 'GV3',
        'avgwindspeed' : 'GV4',
        }

RAIN_DRVS = {
        'rate' : 'ST',
        'hourly' : 'GV0',
        'daily' : 'GV1',
        'weekly' : 'GV2',
        'monthly' : 'GV3',
        'yearly' : 'GV4',
        'maxrate' : 'GV5',
        'yesterday' : 'GV6',
        'total' : 'GV7',
        }

LITE_DRVS = {
        'uv' : 'ST',
        'solar_radiation' : 'GV0',
        'illuminace' : 'GV1'
        }
LITE_EDIT = {
        'uv' : 'I_UV',
        'solar_radiation' : 'I_RADIATION',
        'illuminace' : 'I_LUX'
        }


LTNG_DRVS = {
        'strikes' : 'ST',
        'distance' : 'GV0'
        }

