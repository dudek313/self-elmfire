


#
# ELMFIRE time lagged variables
#

TIME_LAGS_HOURS = {
    "m1"  : 1.0,    #1 hour moisture
    "m10" : 10.0,   #10 hour
    "m100": 100.0,  #100 hour
}


GTIFF_RIO_CONFIG = dict(
        driver="GTiff",
        dtype="float32", 
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
        #predictor=3,
        interleave="band",
        BIGTIFF="IF_SAFER"
)

