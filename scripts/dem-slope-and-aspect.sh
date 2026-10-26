

#code
#/mnt/scratch_lustre/ar_dfdev_scratch/mems2/elmfire/au-elmfire
/mnt/scratch_lustre/ar_dfdev_scratch/mems2/elmfire/self-elmfire


#/mnt/aqf2-scratch1/df-test/efire/data/inputs  
INPUTS_BPATH=/mnt/aqf2-scratch1/df-test/efire/data/inputs/
DERIVED_INPUTS_BPATH=/mnt/aqf2-scratch1/df-test/efire/data/derived-inputs/

mkdir -p "${INPUTS_BPATH}"
mkdir -p "${DERIVED_INPUTS_BPATH}/dem/"

#./scripts/download_data.sh /mnt/aqf2-scratch1/df-test/efire/data/inputs  --dem dems --landcover 2025

./scripts/download_data.sh "${INPUTS_BPATH}" --dem dems,dem --landcover 2019,2020,2024,2025 --canopy meta,glad



#
#create slope and aspect from DEM using gdaldem
#
DEM_S_PATH=${INPUTS_BPATH}/dem/dems1sv1_0.tif
DEM_S_REPROJ_PATH=${DERIVED_INPUTS_BPATH}/dem/derived-30x30m-EPSG-9473--dems1sv1_0.tif

#convert to lat/lon to metric, use bilinear to preserve smooth gradients
#I choose EPSG:9473 as it is best for continental modelling. 
#If local precision is important then use UTM and model subdomains rather than the entire continent
#use -et 0 to disable approximate transformations
#-srcnodata 0: This tells gdalwarp to treat existing NoData values in your input file as 0 during the calculation.
#-dstnodata 0: This ensures that any new edge pixels or empty spaces created by the reprojection warp are also filled and labeled as 0.
#Use PREDICTOR=3 for float32 and PREDICTOR=2 for integer categorical data
# no -of GTiff
gdalwarp \
   -srcnodata 0 -dstnodata 0 -et 0 \
   -s_srs EPSG:4326 -t_srs EPSG:9473 \
   -tr 30 30 -r bilinear \
   -co "BLOCKXSIZE=2048" \
   -co "BLOCKYSIZE=2048" \
   -co "TILED=YES" \
   -co "COMPRESS=ZSTD" \
   -co "PREDICTOR=3" \
   -co "OVERVIEWS=NONE" \
   -co "BIGTIFF=YES" \
   "${DEM_S_PATH}" "${DEM_S_REPROJ_PATH}"

#degrees slope (math degrees rather than geographical degrees)
gdaldem slope \
   -compute_edges -zero_for_flat \
   -co "BLOCKXSIZE=2048" \
   -co "BLOCKYSIZE=2048" \
   -co "TILED=YES" \
   -co "COMPRESS=ZSTD" \
   -co "PREDICTOR=3" \
   -co "OVERVIEWS=NONE" \
   -co "BIGTIFF=YES" \
   "${DEM_S_REPROJ_PATH}" "${DERIVED_INPUTS_BPATH}/dem/derived-30x30m-EPSG-9473--dems1sv1_0--slope-degrees.tif"

#aspect
gdaldem aspect \
   -compute_edges -zero_for_flat \
   -co "BLOCKXSIZE=2048" \
   -co "BLOCKYSIZE=2048" \
   -co "TILED=YES" \
   -co "COMPRESS=ZSTD" \
   -co "PREDICTOR=3" \
   -co "OVERVIEWS=NONE" \
   -co "BIGTIFF=YES" \
   "${DEM_S_REPROJ_PATH}" "${DERIVED_INPUTS_BPATH}/dem/derived-30x30m-EPSG-9473--dems1sv1_0--aspect.tif"

