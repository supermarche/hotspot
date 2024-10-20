import kweb.DivElement
import kweb.ElementCreator
import kweb.state.KVar
import org.slf4j.LoggerFactory
import java.io.File
import java.time.LocalDate
import kotlin.system.exitProcess

class ServerModel(
    val startDateValue: KVar<LocalDate>,
    val startDateText: KVar<String>,
    val endDateValue: KVar<LocalDate>,
    val endDateText: KVar<String>,
    val rasterDaysValue: KVar<Int>,
    val rasterDaysText: KVar<String>,
    val errors:KVar<List<String>>,
    val files:KVar<List<File>>
) {


    lateinit var mapElement: DivElement

    companion object {
        val LOG = LoggerFactory.getLogger(ServerController::class.java)
        fun create(elementCreator: ElementCreator<*>): ServerModel = with(elementCreator) {
            ServerModel(
                startDateValue = kvar(LocalDate.of(2024, 1, 1)),
                startDateText = kvar(""),
                endDateValue = kvar(LocalDate.of(2024, 12, 31)),
                endDateText = kvar(""),
                rasterDaysValue = kvar(1),
                rasterDaysText = kvar(""),
                errors = kvar(emptyList()),
                /* load all Tiff Files */
                files = kvar(File("temp/Urban_Index").let {folder->
                    if(!folder.isDirectory) {
                        LOG.error("Folder $folder does not exist. Exiting.")
                        exitProcess(-1)
                    }
                    val files = folder.listFiles().filter { it.name.endsWith("tiff", true) }
                    if(files.isEmpty()) {
                        LOG.error("No tiff files found in $folder. Exiting.")
                        exitProcess(-1)
                    }

                    files.toList()
                })
            )
        }
    }
}