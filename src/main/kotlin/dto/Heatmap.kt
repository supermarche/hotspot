package dto

import org.locationtech.jts.geom.CoordinateXY
import org.locationtech.jts.geom.GeometryFactory

data class Heatmap(val resolutionInMeter:Double, val dataPoints:List<DataPoint>) {
    companion object {

    }


}
