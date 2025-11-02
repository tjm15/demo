#!/bin/bash
# Import GeoPackage layers into PostGIS using ogr2ogr

set -e

DB_NAME="tpa"
DB_USER="tpa"
DB_HOST="127.0.0.1"
DB_PORT="5432"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <geopackage_files...>"
    exit 1
fi

for gpkg in "$@"; do
    if [ ! -f "$gpkg" ]; then
        echo "Warning: $gpkg not found, skipping"
        continue
    fi
    
    echo "Importing $gpkg..."
    
    # Get layer name from filename
    layer_name=$(basename "$gpkg" .gpkg)
    
    # Import with ogr2ogr (target EPSG:27700)
    ogr2ogr -f PostgreSQL \
        PG:"dbname=$DB_NAME user=$DB_USER host=$DB_HOST port=$DB_PORT" \
        "$gpkg" \
        -nln "layer_geom" \
        -append \
        -t_srs EPSG:27700 \
        -lco GEOMETRY_NAME=geom \
        -lco FID=id
    
    echo "✓ Imported $layer_name"
done

echo "✓ All layers imported"
