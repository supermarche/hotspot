import org.apache.sis.coverage.grid.GridCoverage
import org.apache.sis.coverage.grid.GridGeometry
import org.apache.sis.geometry.GeneralEnvelope
import org.apache.sis.referencing.CommonCRS
import org.apache.sis.storage.*
import org.apache.sis.storage.geotiff.GeoTiffStore
import java.io.File


fun main() {

    val file = File("temp/dgm1_33493_5664_1_sn.tif")


    if (file.exists()) {
        try {
            // Öffne die GeoTIFF-Datei als DataStore
            val store: DataStore = DataStores.open(file)

//            // Überprüfen, ob es sich um einen TIFFStore handelt
            if (store is GeoTiffStore) {
                /*
             * This data store is an aggregate because a GeoTIFF file may contain many images.
             * Not all data stores are aggregate, so the following casts do not apply to all.
             * For this example, we know that the file is GeoTIFF and we take the first image.
             */

                val allImages: MutableCollection<out Resource> = (store as Aggregate).components()
                val firstImage = allImages.iterator().next() as GridCoverageResource

                /*
                * Read the resource immediately and fully.
                */

                var data: GridCoverage = firstImage.read(null);
                System.out.printf("Information about the selected image:%n%s%n", data);


                /*
             * Read only a subset of the resource. The Area Of Interest can be specified
             * in any Coordinate Reference System (CRS). The envelope will be transformed
             * automatically to the CRS of the data (the data are not transformed).
             * This example uses Universal Transverse Mercator (UTM) zone 31 North.
             */
                var areaOfInterest = GeneralEnvelope(CommonCRS.WGS84.universal(49.0, 2.5));
                areaOfInterest.setRange(0, 46600.0, 467000.0);  // Minimal and maximal easting values (metres)
                areaOfInterest.setRange(1, 5427000.0, 5428000.0);       // Minimal and maximal northing values (metres).
                data = firstImage.read(GridGeometry(areaOfInterest));


                System.out.printf(
                    "Information about the resource subset:%n%s%n",
                    data.getGridGeometry().getExtent()
                );


            }
            else {
                println("Die Datei ist kein gültiger TIFFStore.")
            }
        } catch (e: DataStoreException) {
            println("Fehler beim Auslesen der Metadaten: ${e.message}")
        }
    }
    else {
        println("Datei nicht gefunden: $file")
    }
}