/* eslint-disable */
import Map from 'api/Map.js';
import config from 'api/constants.js';
import EPSG2056 from '@geoblocks/proj/src/EPSG_2056.js';
import EPSG21781 from '@geoblocks/proj/src/EPSG_21781.js';


// The URL to the themes service.
config.themesUrl = '{FULL_ENTRY_POINT}themes?version=2&background=background';

// The projection of the map
config.projection = EPSG21781;
// to use the EPSG:2056 projection, replace the previous line with:
// config.projection = EPSG2056;

// The resolutions list.
config.resolutions = [250, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.25, 0.1, 0.05];

// The extent restriction, must be in the same projection as `config.projection`.
// the format is `[minx, miny, maxx, maxy]`for example: `[420000, 30000, 660000, 350000]`
// the default is ǹo restriction.
config.extent = undefined;

// The name of the GeoMapFish layer to use as background. May be a single value
// (WMTS) or a comma-separated list of layer names (WMS).
config.backgroundLayer = 'OSM map';

// end of configuration

const lib = {
  Map
};

export default lib;
