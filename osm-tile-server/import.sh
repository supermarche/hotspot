docker run \
    -e DOWNLOAD_PBF=https://download.geofabrik.de/europe/germany/sachsen-latest.osm.pbf \
    -e DOWNLOAD_POLY=https://download.geofabrik.de/europe/germany.poly \
    -v osm-data:/data/database/ \
    overv/openstreetmap-tile-server \
    import
