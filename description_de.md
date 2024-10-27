## Beschreibung des Projekts zur Identifizierung urbaner Hitzeinseln mit Sentinel-Hub-Satellitendaten

### Projektziel

Das Ziel unseres Projekts war es, städtische Hitzeinseln ("Hotspots") in Görlitz mithilfe von Satellitendaten zu identifizieren, die vom Sentinel Hub bereitgestellt werden.

### Umsetzung

Wir haben eine interaktive Anwendung entwickelt, die es ermöglicht, Satellitendaten für ein ausgewähltes Gebiet und einen bestimmten Zeitraum herunterzuladen und zu analysieren. Die wichtigsten Funktionen der Anwendung sind:

1. **Datenbeschaffung**
   - Automatisierte Abfrage von Satellitendaten über die Sentinel-Hub-API.
   - Integration einer Kartenansicht mit Suchfunktion, um das Zielgebiet einfach zu bestimmen.
   - Festlegung von Zeiträumen und Filterkriterien (z. B. Bewölkungsgrad) für die Datenabfrage.

2. **Datenanalyse**
   - **Berechnung der Landoberflächentemperatur (LST)**
     - Kombination von Sentinel-2- und Sentinel-3-Daten zur Ermittlung der Erdoberflächentemperatur.
   - **Berechnung des Urban Index (UI)**
     - Entwicklung von Methoden zur Identifizierung urbaner Gebiete anhand spektraler Indizes.
   - **Datenverarbeitung**
     - Implementierung von Verfahren zur Glättung von Rasterdaten und zur Aggregation über mehrere Zeiträume, um genauere Ergebnisse zu erzielen.

3. **Ergebnispräsentation**
   - Darstellung der analysierten Daten als GeoTIFF-Dateien.
   - Möglichkeit, die Ergebnisse direkt in der Anwendung zu visualisieren und auf der Karte anzuzeigen.
   - Exportfunktionen für weitere GIS-Analysen.

### Ergebnisse

- Erfolgreiche Erstellung einer Karte der durchschnittlichen Landoberflächentemperaturen für Görlitz.
- Entwicklung von Methoden zur Identifizierung urbaner Strukturen anhand von Satellitendaten.

### Herausforderungen

- **Datenauflösung**
  - Die begrenzte Auflösung der Sentinel-3-Daten erschwerte detaillierte Analysen auf Stadtebene.
- **Wolkenbedeckung**
  - Trotz Filterung konnten nicht alle Störungen durch Wolken beseitigt werden.
- **Datenaggregation**
  - Um aussagekräftige Ergebnisse zu erhalten, mussten wir Daten über vier Jahre mitteln.
- **Unterscheidung von Landflächen**
  - Die Differenzierung zwischen Wasserflächen und Gebäudedächern war schwierig, was zu ungenauen Ergebnissen führte.

### Potenzial und Ausblick

Unser Projekt zeigt das Potenzial von Satellitendaten für die Stadtplanung und Umweltüberwachung. Trotz der aktuellen Einschränkungen sehen wir folgende Möglichkeiten:

- **Verbesserung der Algorithmen**
  - Durch Weiterentwicklung können genauere Ergebnisse erzielt werden, z. B. durch lokale Wolkenbereinigung und Glättung der Sentinel-3-Daten. 
- **Zusätzliche Datenquellen**
  - Die Einbindung von Datensätzen wie Corine Land Cover kann die Identifizierung spezifischer Landnutzungen verbessern.
- **Anwendung in anderen Städten**
  - Die Anwendung kann angepasst werden, um auch in anderen urbanen Gebieten eingesetzt zu werden.

---

## Technische Details

Die Anwendung wurde in Python entwickelt und nutzt Bibliotheken wie Tkinter für die Benutzeroberfläche, rasterio für die Verarbeitung von GeoTIFF-Dateien und die Sentinel-Hub-API für den Zugriff auf Satellitendaten. Interaktive Kartenfunktionen ermöglichen es den Benutzern, das Zielgebiet intuitiv auszuwählen und die Ergebnisse direkt zu visualisieren.

### Berechnung der Landoberflächentemperatur (LST)

1. **NDVI-Berechnung**

   Der Normalized Difference Vegetation Index (NDVI) wurde berechnet, um Vegetationsflächen zu identifizieren:

   $$
   \text{NDVI} = \frac{\text{NIR} - \text{Rot}}{\text{NIR} + \text{Rot}}
   $$

   Dabei sind NIR das nahe Infrarot-Band und Rot das rote Spektralband aus den Sentinel-2-Daten.

2. **Proportionaler Vegetationsanteil (PV)**

   Basierend auf dem NDVI wurde der proportionale Vegetationsanteil PV berechnet:

   - Wenn NDVI < NDVI\_s (0,2): $\text{PV} = 0$
   - Wenn NDVI > NDVI\_v (0,8): $\text{PV} = 1$
   - Ansonsten:

     $$
     \text{PV} = \left( \frac{\text{NDVI} - \text{NDVI}_s}{\text{NDVI}_v - \text{NDVI}_s} \right)^2
     $$

3. **Landoberflächenemissivität (LSE)**

   Die Landoberflächenemissivität wurde wie folgt berechnet:

   - Für NDVI < 0 (Wasser): $\text{LSE} = \varepsilon_{\text{Wasser}} = 0{,}991$
   - Ansonsten:

     $$
     \text{LSE} = \varepsilon_{\text{Vegetation}} \cdot \text{PV} + \varepsilon_{\text{Boden}} \cdot (1 - \text{PV})
     $$

     Dabei sind $\varepsilon_{\text{Vegetation}} = 0{,}973$ und $\varepsilon_{\text{Boden}} = 0{,}966$.

4. **Berechnung der LST**

   Die Landoberflächentemperatur wurde mit folgender Formel berechnet:

   $$
   \text{LST} = \frac{T_{\text{S8}}}{1 + \left( \dfrac{\lambda \cdot T_{\text{S8}}}{\rho} \right) \ln(\text{LSE})}
   $$

   Dabei ist $T_{\text{S8}}$ die Helligkeitstemperatur aus dem Sentinel-3-Band S8, $\lambda = 10{,}85 \times 10^{-6}\,\text{m}$ die Wellenlänge des Bandes und $\rho = 1{,}438 \times 10^{-2}\,\text{m}$ eine Konstante.

### Berechnung des Urban Index (UI)

1. **Berechnung von NDWI und MNDWI**

   - **NDWI (Normalized Difference Water Index)**:

     $$
     \text{NDWI} = \frac{\text{Grün} - \text{NIR}}{\text{Grün} + \text{NIR}}
     $$

   - **MNDWI (Modified NDWI)**:

     $$
     \text{MNDWI} = \frac{\text{Grün} - \text{SWIR}}{\text{Grün} + \text{SWIR}}
     $$

   Dabei sind Grün, NIR und SWIR die entsprechenden Bänder aus den Sentinel-2-Daten.

2. **Wassermaskierung**

   Bereiche mit NDWI oder MNDWI größer als ein Schwellenwert (z. B. 0,3) wurden als Wasser klassifiziert und im UI mit einem Wert von $-0{,}5$ maskiert.

3. **Berechnung des UI**

   Der Urban Index wurde wie folgt berechnet:

   $$
   \text{UI} = \frac{\text{Rot} - \text{NIR}}{\text{Rot} + \text{NIR}}
   $$

4. **Aggregierung**

   Die einzelnen UI-Raster wurden über den Zeitraum mittels Durchschnitt oder Median aggregiert.

---

*Hinweis: Dieses Projekt wurde im Rahmen eines Hackathons entwickelt und befindet sich in einer frühen Entwicklungsphase.*

---

Weitere Details und Notizen finden Sie in der Datei `notes.md`.
