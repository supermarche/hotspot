import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kweb.*
import kweb.plugins.fomanticUI.fomantic
import kweb.state.render

object ServerPage {

    fun ElementCreator<*>.showServerPage() {
        val model = ServerModel.create(this)
        val controller = ServerController(this, model)
        h4().text("Hotmap")
        div(fomantic.ui.container) {
            div(fomantic.ui.form) {
                div(fomantic.fields) {
                    div(fomantic.four.wide.field) {
                        label().text("Datum Von")
                        input() { input ->
                            input.value = model.startDateText
                            input.value.addListener { _, _ ->
                                controller.validate()
                            }
                        }
                    }
                    div(fomantic.four.wide.field) {
                        label().text("Datum bis")
                        input() { input ->
                            input.value = model.endDateText
                            input.value.addListener { _, _ ->
                                controller.validate()
                            }
                        }
                    }
                    div(fomantic.two.wide.field) {
                        label().text("Auflösung")
                        input() { input ->
                            input.value = model.rasterDaysText
                            input.value.addListener { _, _ ->
                                controller.validate()
                            }
                        }
                    }
                }
            }
            render(model.errors) { errors ->
                if (errors.isNotEmpty()) {
                    h4().text("Fehler:")
                    ul {
                        errors.forEach { e ->
                            li().text(e)
                        }
                    }
                }
            }
        }

        model.mapElement = div() {
            it["style"] = "height: 100vh; width: 100%"
        }


        elementScope().launch {
            delay(100)
            controller.loadData()
        }
    }
}

