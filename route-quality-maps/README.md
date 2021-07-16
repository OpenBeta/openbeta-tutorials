## Building sector search maps based on route quality

Examples of how to build interactive sector search maps using Python (Plotly, Mapbox, and Dash). The idea behind these maps is to allow a user to find
sectors with a large number of high-quality routes of the desired type (sport, trad, or both) and in the desired difficulty range.

### Environment

These examples were built and tested using Python 3.8.5, with the following package versions:
* numpy 1.19.2
* pandas 1.1.3
* plotly 5.1.0
* dash 1.20.0

These are the current (7/16/21) default versions installed using Conda. Probably the examples will work with other versions of Python 3 and packages.

### Current Status

These are the files currently included with the example:
* __route_quality_mapping.py__ is a Python script used to create individual interactive .html maps according to filter criteria. The maps display 
areas as points with size corresponding to the number of routes in the area that fulfill the search criteria (type, grade, and minimum quality). 
The areas are also colored by this number (black = few routes that fulfill the criteria, yellow = many routes that fulfill the criteria). Hovering over
each area will display the area name, total number of routes, and the number of routes fulfilling the filter criteria.
* __route_quality_maps_app.py__ is a Python script that runs a Dash app that allows the user to change the filter criteria and rerun. The same information
as described in the previous point is included with each map. Currently the app can be started in debug mode on the users local machine. Just run the Python
script thus:
```
python route_quality_maps_app.py
```
and the output will display a link that can be opened in a browser to display the app.
* __RouteQualityData.pkl.zip__ contains the data used by the above Python scripts.

### Notes

Note that the mapping functions require a Mapbox access token. One of these is provided here, this token may be deleted or changed at any time. Users
are encouraged to get their own access token (free and easy, see https://www.mapbox.com/).
