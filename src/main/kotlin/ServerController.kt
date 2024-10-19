import kotlinx.serialization.json.JsonPrimitive
import kweb.ElementCreator
import java.time.LocalDate

class ServerController(val creator: ElementCreator<*>, val model: ServerModel) {

    fun validate() {
        val errors = mutableListOf<String>()
        try {
            model.startDateValue.value =
                LocalDate.from(Konstanten.DF.parse(model.startDateText.value))
        } catch (e: Exception) {
            errors += "Startdatum ${model.startDateText.value} ungültig. Erwartet wird dd.MM.yyyy. " + e.message
        }

        try {
            model.endDateValue.value = LocalDate.from(Konstanten.DF.parse(model.endDateText.value))
        } catch (e: Exception) {
            errors += "Enddatum ${model.endDateText.value} ungültig. Erwartet wird dd.MM.yyyy. " + e.message
        }
        try {
            model.rasterDaysValue.value = model.rasterDaysText.value.toInt()
        } catch (e:Exception) {
            errors += "Raster ${model.rasterDaysText.value} ungültig. Erwartet wird eine Ganzzahl. " + e.message
        }

        model.errors.value = errors
    }


    fun loadData() {
        val js = """
// Karte initialisieren
var map = L.map('${model.mapElement.id}').setView([51.165691, 10.451526], 6); // Zentriert auf Deutschland

// OpenStreetMap-Layer hinzufügen (Anpassung an den lokalen Tile-Server)
L.tileLayer('http://localhost:8080/tile/{z}/{x}/{y}.png', {
    attribution: 'Tiles &copy; localhost'
}).addTo(map);

// GeoTIFF-Layer laden und hinzufügen
fetch('tif/dgm1_33493_5664_1_sn.tif')
    .then(response => response.arrayBuffer())
    .then(arrayBuffer => {
        parseGeoraster(arrayBuffer).then(georaster => {
            var layer = new GeoRasterLayer({
                georaster: georaster,
                opacity: 0.7,
                resolution: 256
            });
            layer.addTo(map);

            // Karte auf den GeoTIFF-Bereich zoomen
            map.fitBounds(layer.getBounds());
        });
    });
        """.trimIndent()

        creator.browser.callJsFunction(js)
//        creator.browser.callJsFunction(js, JsonPrimitive(model.mapElement.id))


    }


}


//    fun setStartDate(now: LocalDate?) {
//        val date = now ?: LocalDate.now()
//        println("neues Datum ${date}")
//        model.startDateText.value = Konstanten.DF_ISO.format(date)
//        model.startDateValue.value = date
//    }
//
//    fun setEndDate(newDate: LocalDate?) {
//        val date = newDate ?: LocalDate.now()
//        model.endDateText.value = Konstanten.DF_ISO.format(date)
//        model.endDateValue.value = date
//    }

//}