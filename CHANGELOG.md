##### 2.7.rc.27

- Add missing SQLAlchemy variables in compose [c2cgeoportal#9658](https://github.com/camptocamp/c2cgeoportal/pull/9658)

##### 2.7.rc.26

- Do not close the auth panel in first login process [ngeo#8483](https://github.com/camptocamp/ngeo/pull/8483)

##### 2.7.rc.24

- Get only the concerned Transifex resource [ngeo#8478](https://github.com/camptocamp/ngeo/pull/8478)
- Consume event to not redirect the page when clicking on password forgotten link [ngeo#8480](https://github.com/camptocamp/ngeo/pull/8480)

##### 2.7.rc.22

- Fix the theme loading message spinner in Auth panel [ngeo#8469](https://github.com/camptocamp/ngeo/pull/8469)
- Force regenerate the file locales/en/app.json [ngeo#8470](https://github.com/camptocamp/ngeo/pull/8470)
- Fix CSV export with undefined packed_color attribute error [ngeo#8472](https://github.com/camptocamp/ngeo/pull/8472)
- Fix error on LIDAR PNG export with depreciated btoa function [ngeo#8473](https://github.com/camptocamp/ngeo/pull/8473)

##### 2.7.rc.21

- Fix 404 error on en.json [c2cgeoportal#9648](https://github.com/camptocamp/c2cgeoportal/pull/9648)
- Fix the WebComponents source send [ngeo#8464](https://github.com/camptocamp/ngeo/pull/8464)
- Correctly disable the LIDAR button when the panel is collapsed [ngeo#8466](https://github.com/camptocamp/ngeo/pull/8466)

##### 2.7.rc.20

- Add grid-gutter-width to vars.scss [ngeo#8462](https://github.com/camptocamp/ngeo/pull/8462)

##### 2.7.rc.18

- Doc for low-level migrated web components [c2cgeoportal#9642](https://github.com/camptocamp/c2cgeoportal/pull/9642)

##### 2.7.rc.17

- Better documentation for LIDAR profile integration [c2cgeoportal#9620](https://github.com/camptocamp/c2cgeoportal/pull/9620)

##### 2.7.rc.16

- Makes body element focusable for onKeyDown event (for desktop interface) [ngeo#8453](https://github.com/camptocamp/ngeo/pull/8453)

##### 2.7.rc.15

- Fix cypress config and ci workflow [ngeo#8454](https://github.com/camptocamp/ngeo/pull/8454)

##### 2.7.rc.12

- Makes body element focusable for onKeyDown event [ngeo#8439](https://github.com/camptocamp/ngeo/pull/8439)

##### 2.7.rc.10

- [Backport 2.7] Add bufferSize parameter to mapillary options in example [ngeo#8428](https://github.com/camptocamp/ngeo/pull/8428)

##### 2.7.rc.9

- Set grid-gutter-width variable in the CSS [ngeo#8418](https://github.com/camptocamp/ngeo/pull/8418)

##### 2.7.rc.7

- Support regex metadata in themes view [c2cgeoportal#9575](https://github.com/camptocamp/c2cgeoportal/pull/9575)

##### 2.7.rc.6

- Add some other upgrade notes [c2cgeoportal#9572](https://github.com/camptocamp/c2cgeoportal/pull/9572)
- Fix LIDAR profile [ngeo#8388](https://github.com/camptocamp/ngeo/pull/8388)

##### 2.7.rc.5

- Fix changelog [c2cgeoportal#9564](https://github.com/camptocamp/c2cgeoportal/pull/9564)
- Upgrade fix [c2cgeoportal#9566](https://github.com/camptocamp/c2cgeoportal/pull/9566)
- [Backport 2.7] Ignore audit on fast-sass-loader [ngeo#8384](https://github.com/camptocamp/ngeo/pull/8384)
- [Backport 2.7] Fix Mapillary bounding box (configurable value and buffer from map resolution) [ngeo#8387](https://github.com/camptocamp/ngeo/pull/8387)

##### 2.7.rc.4

- Fix changelog [c2cgeoportal#9560](https://github.com/camptocamp/c2cgeoportal/pull/9560)
- Fix password reset and remove theme reloading at password reset [ngeo#8350](https://github.com/camptocamp/ngeo/pull/8350)

##### 2.7.rc.3

- Fix the changelog for Prettier [c2cgeoportal#9556](https://github.com/camptocamp/c2cgeoportal/pull/9556)
- [Backport 2.7] Add gmfSnappingOptions to configure maxFeatures for snapping [ngeo#8347](https://github.com/camptocamp/ngeo/pull/8347)
- Fix Google StreetView panel height [ngeo#8348](https://github.com/camptocamp/ngeo/pull/8348)
- [Backport 2.7] Fix CVE [ngeo#8357](https://github.com/camptocamp/ngeo/pull/8357)

##### 2.7.rc.2

- Have a red crosshare by default [c2cgeoportal#9490](https://github.com/camptocamp/c2cgeoportal/pull/9490)
- Set c2cciutils to latest 1.1 version [c2cgeoportal#9503](https://github.com/camptocamp/c2cgeoportal/pull/9503)
- Add some information in the changelog, add the updated versions [c2cgeoportal#9512](https://github.com/camptocamp/c2cgeoportal/pull/9512)
- Fix translation [c2cgeoportal#9519](https://github.com/camptocamp/c2cgeoportal/pull/9519)
- Fix CVE [c2cgeoportal#9521](https://github.com/camptocamp/c2cgeoportal/pull/9521)
- Fix changelog file creation [c2cgeoportal#9522](https://github.com/camptocamp/c2cgeoportal/pull/9522)
- Add gmfSnappingOptions [c2cgeoportal#9531](https://github.com/camptocamp/c2cgeoportal/pull/9531)
- Fix CVE [c2cgeoportal#9540](https://github.com/camptocamp/c2cgeoportal/pull/9540)
- Don't have double trigger [c2cgeoportal#9544](https://github.com/camptocamp/c2cgeoportal/pull/9544)
- Fix changelog generation [c2cgeoportal#9547](https://github.com/camptocamp/c2cgeoportal/pull/9547)
- [Backport 2.7] Do not overwrite metadata while restoring layertree state [ngeo#8286](https://github.com/camptocamp/ngeo/pull/8286)
- Mapillary panel css fix [ngeo#8294](https://github.com/camptocamp/ngeo/pull/8294)
- Fix missing bottom of the queryresult footer [ngeo#8297](https://github.com/camptocamp/ngeo/pull/8297)
- Add default value for each footer height [ngeo#8308](https://github.com/camptocamp/ngeo/pull/8308)
- Display & hide disclaimers when a layers is visible/hidden [ngeo#8313](https://github.com/camptocamp/ngeo/pull/8313)
- Fix arrows drawing keys for translations [ngeo#8336](https://github.com/camptocamp/ngeo/pull/8336)
