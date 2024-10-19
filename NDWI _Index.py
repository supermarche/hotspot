import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as mpyplot
import os

# Pfad zu deinem .SAFE Ordner
safe_folder = 'S2B_MSIL1C_20241016T100029_N0511_R122_T33UWS_20241016T151956.SAFE/GRANULE/L1C_T33UWS_A039759_20241016T100611/IMG_DATA'

# Lade das Grün-Band (Band 3) und das NIR-Band (Band 8) als .jp2-Dateien
green_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B03.jp2')  # Band 3 (Grün)
nir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B08.jp2')  # Band 8 (NIR)

# Öffne das NIR-Band (10m Auflösung)
with rasterio.open(nir_band_path) as nir_src:
    nir = nir_src.read(1).astype(float)  # 2D-Array (Höhe x Breite)
    nir_transform = nir_src.transform
    nir_profile = nir_src.profile

# Öffne das Grün-Band (20m Auflösung)
with rasterio.open(green_band_path) as green_src:
    # Resample Grün auf die gleiche Auflösung wie NIR (10m)
    green = green_src.read(
        out_shape=(nir_src.height, nir_src.width),  # Neue Größe entsprechend der NIR-Band-Auflösung
        resampling=Resampling.bilinear
    ).astype(float)

# Berechne den NDWI
ndwi = (nir - green) / (nir + green)

# Skaliere den NDWI-Wert auf einen Bereich von -1 bis 1 auf int16
ndwi_scaled = np.clip(ndwi, -1, 1) * 10000  # Multiplizieren, um den Bereich zu vergrößern
ndwi_scaled = ndwi_scaled.astype('int16')  # Konvertiere zu int16

# Speichere den NDWI als GeoTIFF
ndwi_meta = nir_profile
ndwi_meta.update(dtype=rasterio.int16, count=1)

with rasterio.open('ndwi_output.tif', 'w', **ndwi_meta) as dst:
    # Überprüfe sicherheitshalber, ob das NDWI 2D ist und entferne überflüssige Dimensionen
    if ndwi_scaled.ndim == 3:
        ndwi_scaled = np.squeeze(ndwi_scaled, axis=0)

    # Schreibe das 2D-Array
    dst.write(ndwi_scaled, 1)

# Definiere NDWI-Klassen (z.B. Wasser, Nicht Wasser)
ndwi_class = np.zeros_like(ndwi_scaled)
ndwi_class[ndwi_scaled < 0] = 2   # Wasser
ndwi_class[ndwi_scaled >= 0] = 1   # Nicht Wasser

# Visualisierung des NDWI
plt = mpyplot.figure()
img = mpyplot.imshow(ndwi_class[2000:4000, 7000:9000], cmap='Blues')  # Farbkarte für NDWI
plt.colorbar(img)
#plt.title('NDWI-Klassifizierung')
plt.savefig("ndwi_classification.pdf", dpi=1200)
plt.show()
