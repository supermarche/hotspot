import numpy as np
import rasterio
import matplotlib.pyplot as mpyplt

# Funktion, um die Landoberflächentemperatur (LST) zu berechnen
def calculate_lst(band10, emissivity, k1=774.89, k2=1321.08):
    bt = k2 / (np.log((k1 / band10) + 1))
    lst = bt / (1 + (10.8 * bt / 14388) * np.log(emissivity))
    return lst

# Pfade zu den relevanten TIF-Dateien
band10_path = 'l08_file/LC08_L2SP_192024_20240918_20240923_02_T1_ST_B10.TIF'
emissivity_path = 'l08_file/LC08_L2SP_192024_20240918_20240923_02_T1_ST_EMIS.TIF'

# Lade die TIFF-Dateien mit rasterio
with rasterio.open(band10_path) as band10_src:
    band10 = band10_src.read(1)
    band10_meta = band10_src.meta

with rasterio.open(emissivity_path) as emis_src:
    emissivity = emis_src.read(1)

# Berechne die Landoberflächentemperatur (LST)
lst = calculate_lst(band10, emissivity)

# Konvertiere LST von Kelvin nach Celsius
lst_celsius = lst - 144  # Konvertiere in Celsius

# Begrenze die Temperaturwerte auf einen Bereich (z.B. -50°C bis 50°C)
min_temp = 0.25  # Mindestwert für den Plot
max_temp = 2   # Höchstwert für den Plot
lst_celsius_clipped = np.clip(lst_celsius, min_temp, max_temp)

# Finde den Minimal- und Maximalwert der begrenzten LST
lst_min = np.nanmin(lst_celsius_clipped)
lst_max = np.nanmax(lst_celsius_clipped)

# Dynamische Farbabstufung basierend auf dem begrenzten Temperaturbereich
norm = mpyplt.Normalize(vmin=min_temp, vmax=max_temp)

# Visualisierung der LST
plt = mpyplt.figure()
img = mpyplt.imshow(lst_celsius_clipped, cmap='RdYlBu', norm=norm)
#mpyplt.colorbar(img, label="Temperatur (°C)")
mpyplt.colorbar(img)
#mpyplt.title(f"LST (°C) - Min: {lst_min:.2f}°C, Max: {lst_max:.2f}°C")
plt.savefig("1.Heatmap_Landsat_100m.pdf", dpi=1000)
plt.show()
