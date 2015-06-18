package geomapfish

import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._

import java.lang.Math


class Layers extends Simulation {
    val random = new util.Random

    /*
     * CONFIG
     */

    val host = "geomapfish-demo.camptocamp.net"
    val lang = "fr"

    val extent = Array(512691, 149736, 551491, 171836)
    val instance_id = "1.6"
    val resolutions = Array(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200)
    val layers = Array("hotel", "information", "cinema", "bank", "bus_stop", "cafe", "parking", "place_of_worship", "police", "post_office", "restaurant", "zoo", "osm", "osm_time", "line", "polygon", "point", "osm_scale", "hospitals", "firestations", "alpine_hut", "fuel", "osm_time")

    val img_width = 2060
    val img_height = 1215

    val nbUser = 1
    val spaceTime = 2

    /*
     * /CONFIG
     */

    val rampTime = nbUser * spaceTime

    val cache_version = random.nextInt()
    val defaults_feeder = Array(Map(
        "instance_id" -> instance_id
    )).random

    def randX: Int = extent.get(0) + random.nextInt(extent.get(2) - extent.get(0))
    def randY: Int = extent.get(1) + random.nextInt(extent.get(3) - extent.get(1))
    def getBbox(width: Int, height: Int)(x: Int, y: Int, resolution: Double): String = {
        val x2 = x + width * resolution
        val y2 = y + height * resolution
        "%d,%d,%f,%f".format(x, y, x2, y2)
    }
    val common_bbox = getBbox(img_width, img_height)_


    val map_feeder = new Feeder[String] {
        // always return true as this feeder can be polled infinitively
        override def hasNext = true
        override def next: Map[String, String] = {
            resolutions.map(resolution =>
               ("BBOX_%.3f".format(resolution), common_bbox(randX, randY, resolution))
            ).toMap
        }
    }

    val httpProtocol = http
        .baseURL("http://" + host)
        .inferHtmlResources(WhiteList("http://" + host + "/*"), BlackList())
        .acceptHeader("image/png,image/*;q=0.8,*/*;q=0.5")
        .acceptEncodingHeader("gzip, deflate")
        .acceptLanguageHeader(lang + ";q=0.5")
        .connection("keep-alive")
        .contentTypeHeader("application/x-www-form-urlencoded; charset=UTF-8")
        .userAgentHeader("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0")

    val headers = Map(
        "Accept" -> "*/*",
        "Pragma" -> "no-cache"
    )

    val scn1 = scenario("LayersPerformances")
        .feed(defaults_feeder)
        .feed(map_feeder)
    val scn2 = layers.foldLeft(scn1) { (s1, layer) =>
        resolutions.foldLeft(s1) { (s2, resolution) =>
            s2.exec(
                    http("%s_%.3f".format(layer, resolution))
                    .get("/${instance_id}/wsgi/mapserv_proxy")
                    .queryParam("SERVICE", "WMS")
                    .queryParam("VERSION", "1.1.1")
                    .queryParam("REQUEST", "GetMap")
                    .queryParam("FORMAT", "image/png")
                    .queryParam("TRANSPARENT", "TRUE")
                    .queryParam("LAYERS", layer)
                    .queryParam("STYLES", "")
                    .queryParam("SRS", "EPSG:21781")
                    .queryParam("BBOX", "BBOX_%.3f".format(resolution))
                    .queryParam("WIDTH", img_width)
                    .queryParam("HEIGHT", img_height)
                    .headers(headers))
                .pause(1)
        }
    }

    setUp(scn2.inject(rampUsers(nbUser) over (rampTime seconds))).protocols(httpProtocol)
}
