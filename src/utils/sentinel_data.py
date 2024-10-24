import os
from pathlib import Path

from sentinelhub import BBox, CRS, MimeType, SentinelHubRequest, DataCollection, SentinelHubCatalog, bbox_to_dimensions, \
    MosaickingOrder
from src.utils.config import load_config
from src.utils.gis_helpers import save_tiff_and_metadata
from rasterio.transform import from_bounds

from src.utils.helper_functions import normalize_to_weeks


class SentinelData:
    def __init__(self):
        self.config = load_config()

    def download_sentinel2_data(self, bbox_coordinates, crs, date_range, resolution):
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{ bands: ["B03", "B04", "B08", "B11"], units: ["REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE"]}],
                output: { bands: 4, sampleType: "FLOAT32" }
            };
        }
    
        function evaluatePixel(sample) {
            return [sample.B03, sample.B04, sample.B08, sample.B11];
        }
        """

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C.define_from("s2l1c", service_url=self.config.sh_base_url),
                    time_interval=date_range,
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=BBox(bbox_coordinates, crs=CRS(crs)),
            resolution=(resolution, resolution),
            config=self.config
        )

        return request.get_data()[0]

    def download_sentinel3_data(self, bbox_coordinates, crs, date_range, resolution):
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{ bands: ["S8", "S9"], units: ["BRIGHTNESS_TEMPERATURE", "BRIGHTNESS_TEMPERATURE"] }],
                output: { bands: 2, sampleType: "FLOAT32" }
            };
        }
    
        function evaluatePixel(sample) {
            return [sample.S8, sample.S9];
        }
        """

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL3_SLSTR.define_from("s3slstr", service_url=self.config.sh_base_url),
                    time_interval=date_range
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=BBox(bbox_coordinates, crs=CRS(crs)),
            resolution=(resolution, resolution),
            config=self.config
        )

        return request.get_data()[0]

    def search_data(self, bbox_coordinates, crs, date_range, filter='eo:cloud_cover < 50'):
        aoi_bbox = BBox(bbox_coordinates, crs=CRS(crs))
        catalog = SentinelHubCatalog(config=self.config)

        sentinel2_search = catalog.search(DataCollection.SENTINEL2_L2A, bbox=aoi_bbox, time=date_range,
                                          filter=filter, )
        sentinel3_search = catalog.search(DataCollection.SENTINEL3_SLSTR, bbox=aoi_bbox, time=date_range,
                                          filter=filter, )

        dates_sentinel2 = set([item['properties']['datetime'][:10] for item in sentinel2_search])
        dates_sentinel3 = set([item['properties']['datetime'][:10] for item in sentinel3_search])
        common_dates = list(sorted(dates_sentinel2.intersection(dates_sentinel3)))

        return {"sentinel_2": dates_sentinel2, "sentinel_3": dates_sentinel3, "common_dates": common_dates}

    def download_s2_s3_data_pack(self, bbox_coordinates, crs, date_range, resolution, out_dir, filter='eo:cloud_cover < 50'):

        available_data = self.search_data(bbox_coordinates, crs, date_range, filter=filter)
        aoi_bbox = BBox(bbox=bbox_coordinates, crs=CRS(crs))
        aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)
        transform = from_bounds(*aoi_bbox, aoi_size[0], aoi_size[1])
        bands_metadata_sentinel2 = {"bands": ["B03", "B04", "B08", "B11"]}
        Path(os.path.join(out_dir,"Sentinel-2")).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(out_dir, "Sentinel-3")).mkdir(parents=True, exist_ok=True)

        for day in available_data['common_dates']:
            current_day_range = (day+'T00:00:00Z', day+'T23:59:59.9Z')
            sentinel_2_data_array = self.download_sentinel2_data(bbox_coordinates, crs, current_day_range, resolution)
            save_tiff_and_metadata(sentinel_2_data_array, transform, crs, f"{out_dir}/Sentinel-2/s2_{day}.tiff", bands_metadata_sentinel2)

            sentinel_3_data_array = self.download_sentinel3_data(bbox_coordinates, crs, current_day_range, resolution)
            save_tiff_and_metadata(sentinel_3_data_array, transform, crs, f"{out_dir}/Sentinel-3/s3_{day}.tiff",
                                   bands_metadata_sentinel2)

    def download_s2_data_weekly(self, bbox_coordinates, crs, date_range, resolution, out_dir):
        aoi_bbox = BBox(bbox=bbox_coordinates, crs=CRS(crs))
        aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)
        transform = from_bounds(*aoi_bbox, aoi_size[0], aoi_size[1])
        bands_metadata_sentinel2 = {"bands": ["B03", "B04", "B08", "B11"]}
        Path(os.path.join(out_dir, "Sentinel-2-weeks")).mkdir(parents=True, exist_ok=True)
        weeks = normalize_to_weeks(date_range)
        for week in weeks:
            sentinel_2_mosaic_data_array = self.download_sentinel2_data(bbox_coordinates, crs, week, resolution)
            save_tiff_and_metadata(sentinel_2_mosaic_data_array, transform, crs, f"{out_dir}/Sentinel-2-weeks/s2_{week[0]}-{week[1]}.tiff",
                                   bands_metadata_sentinel2)
