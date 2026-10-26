#!/bin/bash
# Download the continental Australian datasets used by au-elmfire into a local data store.
#
# Usage:
#   scripts/download_data.sh DATA_ROOT [options]
#
# Options:
#   --dem LIST          GA 1" DEM variants: any of dems,dem,demh, or none   (default: dems)
#   --landcover YEARS   DEA Land Cover years, comma separated, or none     (default: 2024)
#   --canopy LIST       meta (Meta/WRI 1 m CHM aggregated to ~25 m, 10-deg tiles, verified, 7 GB),
#                       glad (GLAD 2019 30 m, URL unverified), or none     (default: meta)
#   --nvis SOURCE       NVIS MVG raster: a URL or local path (zip/gdb/tif) to fetch and keep
#                       under DATA_ROOT/nvis/ (no stable direct URL; see docs/DATA.md)
#   --dry-run           print what would be downloaded
#
# Downloads resume (curl -C -) and retry. If the AWS CLI is installed, S3 objects are
# fetched with `aws s3 cp --no-sign-request`, which is faster for the 35-45 GB DEM files.
#
# Sizes: DEM-S 38.3 GB, DEM 34.5 GB, DEM-H 38.4 GB, Land Cover L4 ~2.1 GB per year,
# Meta CHM avg tiles 7.0 GB total (17 tiles, 20-980 MB each), GLAD ~1.5 GB. After downloading, run
#   au-elmfire-prep catalog DATA_ROOT
# (and optionally `au-elmfire-prep terrain ...`, `nvis ...`, `canopy ...`; see docs/DATA.md).
set -euo pipefail

ROOT=${1:?usage: $0 DATA_ROOT [--dem dems,dem,demh] [--landcover 2024,...] [--canopy meta|glad] [--nvis SRC]}
shift
DEM=dems; LANDCOVER=2024; CANOPY=meta; NVIS=""; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dem) DEM=$2; shift 2 ;;
    --landcover) LANDCOVER=$2; shift 2 ;;
    --canopy) CANOPY=$2; shift 2 ;;
    --nvis) NVIS=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done

DEA=https://dea-public-data.s3.ap-southeast-2.amazonaws.com
DEM_BASE=$DEA/projects/elevation/ga_srtm_dem1sv1_0
LC_BASE=$DEA/derivative/ga_ls_landcover_class_cyear_3/2-0-0/continental_mosaics
META_BASE=https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float_epsg4326_v3_10deg
GLAD_URLS=("https://glad.umd.edu/Potapov/Forest_height_2019/Forest_height_2019_AUS.tif"
           "https://glad.geog.umd.edu/Potapov/Forest_height_2019/Forest_height_2019_AUS.tif")

fetch() {   # fetch URL DEST
  local url=$1 dest=$2
  if [ "$DRY" = 1 ]; then echo "would fetch $url -> $dest"; return 0; fi
  mkdir -p "$(dirname "$dest")"
  if [ -s "$dest" ] && [ ! -e "$dest.part" ]; then echo "exists: $dest"; return 0; fi
  echo "fetching $url"
  if command -v aws >/dev/null && [[ $url == https://*.s3*.amazonaws.com/* ]]; then
    local bucket key
    bucket=$(echo "$url" | sed -E 's#https://([^.]+)\.s3[^/]*\.amazonaws\.com/.*#\1#')
    key=$(echo "$url" | sed -E 's#https://[^/]+/##')
    aws s3 cp --no-sign-request "s3://$bucket/$key" "$dest.part" && mv "$dest.part" "$dest" && return 0
  fi
  curl -fL --retry 10 --retry-delay 10 --retry-all-errors -C - -o "$dest.part" "$url"
  mv "$dest.part" "$dest"
}

# 1. GA SRTM-derived 1 second DEMs (national COGs, EPSG:4326, Float32, CC BY 4.0)
for v in ${DEM//,/ }; do
  case "$v" in
    dems) fetch "$DEM_BASE/dems1sv1_0.tif" "$ROOT/dem/dems1sv1_0.tif" ;;
    dem)  fetch "$DEM_BASE/dem1sv1_0.tif"  "$ROOT/dem/dem1sv1_0.tif" ;;
    demh) fetch "$DEM_BASE/demh1sv1_0.tif" "$ROOT/dem/demh1sv1_0.tif" ;;
    none) ;;
    *) echo "unknown DEM variant $v" >&2; exit 1 ;;
  esac
done
[ "$DEM" != none ] && [ "$DRY" = 0 ] && fetch "$DEM_BASE/README.txt" "$ROOT/dem/README.txt"

# 2. DEA Land Cover Level 4 continental mosaics (EPSG:3577, 30 m, uint8, nodata 255, CC BY 4.0)
if [ "$LANDCOVER" != none ]; then
  for y in ${LANDCOVER//,/ }; do
    f=ga_ls_landcover_class_cyear_3_mosaic_${y}--P1Y_level4.tif
    fetch "$LC_BASE/${y}--P1Y/$f" "$ROOT/landcover/$f"
  done
fi

# 3. Canopy height
for c in ${CANOPY//,/ }; do
  case "$c" in
    meta)  # Meta/WRI CHM, mean height per ~25 m cell, UInt16 cm, nodata 65535, EPSG:4326, CC BY 4.0
      for lat in -10.0 -20.0 -30.0 -40.0; do
        for lon in 110.0 120.0 130.0 140.0 150.0; do
          f="meta_chm_lat=${lat}_lon=${lon}_avg.tif"
          if [ "$DRY" = 1 ] || curl -fsS -I -o /dev/null "$META_BASE/$f"; then
            fetch "$META_BASE/$f" "$ROOT/canopy/meta_chm_avg/$f"
          fi   # ocean-only tiles (lat -40, lon 110-130) do not exist
        done
      done ;;
    glad)  # GLAD Global Forest Canopy Height 2019, Australia file (URL from GLAD's page, unverified)
      ok=0
      for u in "${GLAD_URLS[@]}"; do fetch "$u" "$ROOT/canopy/glad/Forest_height_2019_AUS.tif" && ok=1 && break; done
      [ $ok = 1 ] || echo "GLAD download failed; get Forest_height_2019_AUS.tif from https://glad.umd.edu/dataset/gedi" >&2 ;;
    none) ;;
    *) echo "unknown canopy source $c" >&2; exit 1 ;;
  esac
done

# 4. NVIS (manual source: https://fed.dcceew.gov.au/datasets/5e70b5afc36a4c458a2cceb313eb3889/about)
if [ -n "$NVIS" ]; then
  if [[ $NVIS == http* ]]; then fetch "$NVIS" "$ROOT/nvis/$(basename "${NVIS%%\?*}")"
  else mkdir -p "$ROOT/nvis"; cp -r "$NVIS" "$ROOT/nvis/"; fi
  echo "Next: au-elmfire-prep nvis --src $ROOT/nvis/<file> --out $ROOT/nvis/nvis_mvg_extant.tif"
fi

echo "Done. Next: au-elmfire-prep catalog $ROOT"
