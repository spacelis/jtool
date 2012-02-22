#!/home/wenli/devel/python/python
# -*- coding: utf-8 -*-
"""File: gmap.py
Description:
    A module for compose HTML using Google Maps API to draw customized maps
History:
    0.1.0 The first version.
"""
__version__ = '0.1.0'
__author__ = 'SpaceLis'

import textwrap

_HTMLFRAME = textwrap.dedent(r'''<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <style type="text/css">
      html { height: 100%% }
      body { height: 100%%; margin: 0; padding: 0 }
      #map_canvas { height: 100%% }
    </style>
    <script type="text/javascript"
      src="http://maps.googleapis.com/maps/api/js?key=%(apikey)s&sensor=%(sensor)s">
    </script>
    <script type="text/javascript">
      function initialize() {
        var options = {
          center: %(mapcenter)s,
          zoom: 8,
          mapTypeId: google.maps.MapTypeId.%(maptype)s
        };
        var map = new google.maps.Map(document.getElementById("map_canvas"),
            options);
<!-- Genereated code V-->
%(generated)s
<!-- Genereated code ^-->
      }
    </script>
  </head>
  <body onload="initialize()">
    <div id="map_canvas" style="width:100%%; height:100%%"></div>
  </body>
</html>''')


class GMObject(object):
    """ A base object for identifying objects for Google Maps
    """
    @staticmethod
    def js_helper(val):
        """ return js_code universally
        """
        if isinstance(val, GMObject):
            return val.js_code()
        if isinstance(val, int) or isinstance(val, float):
            return str(val)
        elif isinstance(val, str):
            return val
        elif isinstance(val, list):
            return '[\n%s\n]' % (',\n'.join([GMObject.js_helper(v) for v in val]),)
        elif isinstance(val, dict):
            return '{\n%s\n}' % (',\n'.join([': '.join([k, GMObject.js_helper(v)]) for k, v in val.iteritems()]),)
        else:
            raise TypeError('Do not know how to translate: %s' % (val.__class__,))

    def __init__(self):
        super(GMObject, self).__init__()

    def js_code(self):
        """ Must to be implement for translating
        """
        raise NotImplementedError

class GMOverlay(GMObject):
    """ A base class for identifying objects drawable
    """
    def __init__(self):
        super(GMOverlay, self).__init__()


class GMLatLng(GMObject):
    """ A LatLng pythong interface
    """
    def __init__(self, lat, lng):
        super(GMLatLng, self).__init__()
        self.lat = lat
        self.lng = lng

    def js_code(self):
        """ Generate Javascript code for this object
        """
        return 'new google.maps.LatLng(%s,%s)' % (self.lat, self.lng)

class GMMarker(GMOverlay):
    """ An interface for Marker
    """
    _OPTION_LIST = ['icon', 'title', 'shape']

    def __init__(self, *args, **kargs):
        super(GMMarker, self).__init__()
        if len(args) >= 2:
            self.position = GMLatLng(args[0], args[1])
        elif len(args) >=1:
            self.position = args[0]
        elif 'lat' in kargs and 'lng' in kargs:
            self.position = GMLatLng(kargs['lat'], kargs['lng'])
        elif 'position' in kargs:
            self.position = kargs['position']
        else:
            raise ValueError('No position specified for a Marker')

        self.options = {'map': 'map'}
        for o in GMMarker._OPTION_LIST:
            if o in kargs:
                self.options[o] = kargs[o]

    def js_code(self):
        """ Generate Javascript code for this object
        """
        self.options['position'] = self.position.js_code()
        js = 'new google.maps.Marker(%s)' % (GMObject.js_helper(self.options),)
        return js

class GMPolyline(GMOverlay):
    """ A python interface for polygon type in Google Maps API
    """
    _OPTION_LIST = {'strokeColor', 'strokeOpacity', 'strokeWeight'}

    def __init__(self, **kargs):
        super(GMPolyline, self).__init__()
        self.path = list()
        self.options = {'map': 'map'}
        self.position = None
        for o in GMMarker._OPTION_LIST:
            if o in kargs:
                self.options[o] = kargs[o]


    def add_point(self, latlng):
        """ add a new point in the path
        """
        if isinstance(latlng, GMLatLng):
            if not self.position:
                self.position = latlng
            self.path.append(latlng)
        else:
            raise TypeError('Types other then GMLatLng is not supported')

    def js_code(self):
        """ Generate Javascript code for this object
        """
        if not self.position:
            raise ValueError('The path has no points')
        self.options['path'] = self.path
        js = 'new google.maps.Polyline(%s)' % (GMObject.js_helper(self.options),)
        return js

class GMPolylineWithMarkers(GMPolyline):
    """ A combined version of polylines and markers
    """
    def __init__(self, **kargs):
        super(GMPolylineWithMarkers, self).__init__(**kargs)
        self.markerss = list()

    def add_point(self, latlng):
        """ add a new point for this polyline with a marker
        """
        super(GMPolylineWithMarkers, self).add_point(latlng)
        self.markers.append(GMMarker(latlng))

    def js_code(self):
        """ Generate Javascript code for this object
        """
        js = super(GMPolylineWithMarkers, self).js_code() + '\n'
        js += '\n'.join([v.js_code() for v in self.markers]) + '\n'
        return js



class GMap(GMObject):
    """ A class representing Google map
    """
    _DEFAULTCONFIG = {
        'apikey': 'AIzaSyCZyU1PER77rHKYfZXC2sE-N2PzLieRz88',
        'sensor': 'false',
        'mapcenter': GMLatLng(-34.397, 150.644).js_code(),
        'maptype': 'ROADMAP'
    }

    def __init__(self, **kargs):
        super(GMap, self).__init__()
        self.config = GMap._DEFAULTCONFIG
        self.frame = _HTMLFRAME
        self.config.update(kargs)
        self.overlays = list()

    def add_overlay(self, overlay):
        """docstring for add_marker
        """
        if isinstance(overlay, GMOverlay):
            self.overlays.append(overlay)
        else:
            raise ValueError('The overlay type is not supported.')

    def js_code(self):
        """ Generate Javascript code for this object
        """
        return ';\n'.join([GMObject.js_helper(o) for o in self.overlays]) + ';\n'

    def html_code(self):
        """ Generate HTML code for a Google Map
        """
        self.config.update({'generated': self.js_code()})
        if len(self.overlays) > 0:
            self.config.update({'mapcenter': self.overlays[0].position.js_code()})
        return self.frame % self.config

    def write_html(self, fout):
        """ Write the HTML code
        """
        if not isinstance(fout, file):
            fout = open(fout, 'w')
        print >> fout, self.html_code(),

def console():
    """ Draw maps with input data from console
    """
    parser = argparse.ArgumentParser(description='Draw markers or Polylines on Google Maps',
            epilog='NOTE: Default drawing type is markers.')
    parser.add_argument('-p', '--polyline', dest='polyline', action='store_true', default=False,
            help='Draw polylines.')
    parser.add_argument('-o', '--output', dest='output', action='store', metavar='FILE', default=None,
            help='The output html filename.')
    parser.add_argument('sources', metavar='FILE', nargs='*',
            help='Input files. Those end with .gz will be open as GZIP files.')
    args = parser.parse_args()
    if len(args.sources) > 0:
        args.fin = FileInputSet(args.sources)
    else:
        args.fin = sys.stdin

    if args.output:
        args.fout = open(args.output, 'w')
    else:
        logging.error('No output file specified')
        exit(1)

def test():
    """docstring for test
    """
    g = GMap()
    p = GMPolylineWithMarkers()
    p.add_point(GMLatLng(52.009824, 4.361659))
    p.add_point(GMLatLng(51.009824, 4.361659))
    g.add_overlay(p)
    g.write_html('test.html')

if __name__ == '__main__':
    test()




