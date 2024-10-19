docker run -d -p 8080:80 --name osmtileserver -v osm-data:/data/database/ -v osm-tiles:/data/tiles/ overv/openstreetmap-tile-server run
