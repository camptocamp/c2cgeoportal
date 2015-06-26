package geomapfish

import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._

import java.lang.Math


class Test extends Simulation {
    val random = new util.Random

    val host = "geomapfish-demo.camptocamp.net"
    val lang = "fr"
    //val instance_ids = (0 to 29).map { n => n.toString }
    val instance_ids = Array("1.6")

    val httpProtocol = http
        .baseURL("http://" + host)
        .inferHtmlResources(WhiteList("http://" + host + "/*"), BlackList())
        .acceptHeader("image/png,image/*;q=0.8,*/*;q=0.5")
        .acceptEncodingHeader("gzip, deflate")
        .acceptLanguageHeader(lang + ";q=0.5")
        .connection("keep-alive")
        .contentTypeHeader("application/x-www-form-urlencoded; charset=UTF-8")
        .userAgentHeader("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0")

    val headers_0 = Map(
        "Accept" -> "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    )

    val scn = instance_ids.foldLeft(scenario("JustTest")) { (s, instance_id) =>
        s.exec(http("index").get("/" + instance_id + "/").headers(headers_0)).pause(1)
    }

    setUp(scn.inject(rampUsers(1) over (1 seconds))).protocols(httpProtocol)
}
