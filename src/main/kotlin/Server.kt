import ServerPage.showServerPage
import kweb.Kweb
import kweb.new
import kweb.plugins.fomanticUI.FomanticUIPlugin
import kweb.plugins.staticFiles.ResourceFolder
import kweb.plugins.staticFiles.StaticFilesPlugin
import java.io.File

fun main() {
    Kweb(port = 16097,
        debug = true,
        plugins = listOf(FomanticUIPlugin(),
            StaticFilesPlugin(ResourceFolder("js"), "/js"),
            StaticFilesPlugin(ResourceFolder("css"), "/css"),
            StaticFilesPlugin(ResourceFolder("tif"), "/tif")

        )) {
        doc.head {
//            <link rel="stylesheet" href="css/styles.css">
//            <script type="application/javascript" src="js/leaflet.js"></script>
//            <script type="application/javascript" src="js/geotiff.js"></script>
//            <script type="application/javascript" src="js/georaster.js"></script>
//            <script type="application/javascript" src="js/georaster-layer-for-leaflet.js"></script>
            element("link") {
                it["rel"] = "stylesheet"
                it["href"] = "css/leaflet.css"
            }
            element("script") {
                it["type"] = "application/javascript"
                it ["src"] = "js/leaflet.js"
            }
            element("script") {
                it["type"] = "application/javascript"
                it ["src"] = "js/geotiff.js"
            }
            element("script") {
                it["type"] = "application/javascript"
                it ["src"] = "js/georaster.js"
            }
            element("script") {
                it["type"] = "application/javascript"
                it ["src"] = "js/georaster-layer-for-leaflet.js"
            }
        }

        doc.body.new {
            showServerPage()
        }
    }
}