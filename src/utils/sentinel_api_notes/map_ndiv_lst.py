import rasterio
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from rasterio.plot import reshape_as_raster, reshape_as_image

def read_file(date, band, satellite):
    base_path = "../data/{band}_{date}_{satellite}.tiff"
    # Öffne das Rot-Band (10m Auflösung)
    with rasterio.open(base_path.format(band=band, date=date, satellite=satellite)) as img:
        data = img.read()  # 2D-Array (Höhe x Breite)
    return data

def calculate_ndvi(nir, red):
    # Berechne den NDVI
    return  ((nir - red) / (nir + red))

def calculate_lst(b4, b8, s8):
    # see https://custom-scripts.sentinel-hub.com/sentinel-3/land_surface_temperature/
    ndvis = 0.2
    ndviv = 0.8 # 0.5-0.8

    # emissivity
    waterE = 0.991
    soilE = 0.966
    vegetationE = 0.973
    C = 0.009 #surface roughness, https://www.researchgate.net/publication/331047755_Land_Surface_Temperature_Retrieval_from_LANDSAT-8_Thermal_Infrared_Sensor_Data_and_Validation_with_Infrared_Thermometer_Camera

    # central/mean wavelength in meters, Sentinel-3 SLSTR B08 (almost the same as Landsat B10)
    bCent = 0.000010854

    # rho =h*c/sigma=PlanckC*velocityLight/BoltzmannC
    rho = 0.01438 # m K

    def LSEcalc(ndvi_p, pv):
        if (ndvi_p < 0):
            #water
            LSE = waterE
        elif (ndvi_p < ndvis):
            #soil
            LSE = soilE;
        elif (ndvi_p > ndviv):
            #vegetation
            LSE = vegetationE;
        else:
            #mixtures of vegetation and soil
            LSE = vegetationE * pv + soilE * (1 - pv) + C;

        return LSE

    size = 2000
    img = np.zeros((size, size))

    for i in range(size):
        print(i)
        for j in range(size):
            if (s8[i,j] > 173 and s8[i,j] < 65000 and b4[i,j] > 0 and b8[i,j] > 0):
                # ok image
                # in K
                S8BTi = s8[i,j]

                # 2 NDVI - Normalized Difference vegetation Index - based on this custom script: https://custom-scripts.sentinel-hub.com/sentinel-3/ndvi/
                NDVIi = (b8[i,j] - b4[i,j]) / (b8[i,j] + b4[i,j])

                # 3 PV - proportional vegetation
                PVi = ((NDVIi - ndvis) / (ndviv - ndvis)) ** 2

                # 4 LSE land surface emmisivity
                LSEi = LSEcalc(NDVIi, PVi)

                #5 LST
                LSTi = S8BTi / (1 +  ((bCent * S8BTi) / rho) * np.log(LSEi))

                img[i,j] = LSTi
            else:
                img[i,j] = np.nan
    return img

if __name__ == "__main__":
    fig = plt.figure()
    b04 = read_file("2024-04-12", "B04", "sentinel-2-l2a")
    b08 = read_file("2024-04-12", "B08", "sentinel-2-l2a")
    s8 = read_file("2024-04-12", "S8", "sentinel-3-slstr")

    lst = calculate_lst(b04[0,:,:], b08[0,:,:], s8[0,:,:])
    print(np.min(lst), np.max(lst))
    pmap = plt.imshow(lst)
    fig.colorbar(pmap)
    plt.show()