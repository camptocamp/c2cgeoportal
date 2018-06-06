<?xml version="1.0" encoding="UTF-8"?>
<!--
  ~ Copyright (C) 2014-2018  Camptocamp
  ~
  ~ This file is part of MapFish Print
  ~
  ~ MapFish Print is free software: you can redistribute it and/or modify
  ~ it under the terms of the GNU General Public License as published by
  ~ the Free Software Foundation, either version 3 of the License, or
  ~ (at your option) any later version.
  ~
  ~ MapFish Print is distributed in the hope that it will be useful,
  ~ but WITHOUT ANY WARRANTY; without even the implied warranty of
  ~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  ~ GNU General Public License for more details.
  ~
  ~ You should have received a copy of the GNU General Public License
  ~ along with MapFish Print.  If not, see <http://www.gnu.org/licenses/>.
  -->

<configuration>

    <appender name="standardOut" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <Pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</Pattern>
        </encoder>
    </appender>

    <appender name="File" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/${instanceid}.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <!-- daily rollover -->
            <fileNamePattern>logs/${instanceid}.%d{yyyy-MM-dd}.log</fileNamePattern>

            <!-- keep 7 days' worth of history -->
            <maxHistory>7</maxHistory>
        </rollingPolicy>

        <encoder>
            <Pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</Pattern>
        </encoder>
    </appender>

    <logger name="org.mapfish" level="${"DEBUG" if development == "TRUE" else "WARN"}" />
    <logger name="net.sf.jasperreports" level="WARN" />
    <logger name="org.springframework" level="WARN" />
    <logger name="org.apache" level="WARN" />
    <!-- Set spec logger to DEBUG to log all print spec json data -->
    <logger name="org.mapfish.print.servlet.BaseMapServlet.spec" level="OFF" />
    <logger name="com.codahale.metrics" level="INFO" />
    <logger name="com.codahale.metrics.JmxReporter" level="INFO" />


    <root level="ALL">
        <appender-ref ref="standardOut" />
        <appender-ref ref="File" />
    </root>
</configuration>
