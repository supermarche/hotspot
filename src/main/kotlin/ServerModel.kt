import kweb.DivElement
import kweb.ElementCreator
import kweb.state.KVar
import java.time.LocalDate

class ServerModel(
    val startDateValue: KVar<LocalDate>,
    val startDateText: KVar<String>,
    val endDateValue: KVar<LocalDate>,
    val endDateText: KVar<String>,
    val rasterDaysValue: KVar<Int>,
    val rasterDaysText: KVar<String>,
    val errors:KVar<List<String>>
) {


    lateinit var mapElement: DivElement

    companion object {
        fun create(elementCreator: ElementCreator<*>): ServerModel = with(elementCreator) {
            ServerModel(
                startDateValue = kvar(LocalDate.of(2024, 1, 1)),
                startDateText = kvar(""),
                endDateValue = kvar(LocalDate.of(2024, 12, 31)),
                endDateText = kvar(""),
                rasterDaysValue = kvar(1),
                rasterDaysText = kvar(""),
                errors = kvar(emptyList())
            )
        }
    }
}