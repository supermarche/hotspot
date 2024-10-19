package dto

import org.locationtech.jts.geom.CoordinateXY
import org.locationtech.jts.geom.GeometryFactory

data class DataPoint(val x:Double, val y:Double, val value:Double) {
    companion object {
        val geometryFactory = GeometryFactory()
    }

    val point = geometryFactory.createPoint(CoordinateXY(x, y))
}


