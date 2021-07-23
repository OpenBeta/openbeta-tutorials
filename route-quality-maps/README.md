## Building sector search maps based on route quality

Examples of how to build interactive sector search maps using Python (Plotly, Mapbox, and Dash). The idea behind these maps is to allow a user to find
sectors with a large number of high-quality routes of the desired type (sport, trad, or both) and in the desired difficulty range.

### Environment and installation instructions

These examples were built and tested using Python 3.8.5, the required packages can be installed in a Python virtual environment (after installing virtualenv), thus:

```
cd /path/to/openbeta-tutorials-master/route-quality-maps
virtualenv env --python=python3.8.5
source env/bin/activate
pip3 install -r requirements.txt
```

### Current Status

These are the files currently included with the example:
* __route_quality_map_generation.py__ is a Python script used to create individual interactive .html maps according to filter criteria. The maps display 
areas as points with size corresponding to the number of routes in the area that fulfill the search criteria (type, grade, and minimum quality). 
The areas are also colored by this number (black = few routes that fulfill the criteria, yellow = many routes that fulfill the criteria). Hovering over
each area will display the area name, total number of routes, and the number of routes fulfilling the filter criteria.
* __route_quality_maps_app.py__ is a Python script that runs a Dash app that allows the user to change the filter criteria and rerun. The same information
as described in the previous point is included with each map. The app can be started on the user's local machine like this:
```
python route_quality_map_app.py
```
* Or, there is a live demo of this app [here](https://rqm.openbeta.io/).
* __RouteQualityData.pkl.zip__ contains the data used by the above Python scripts see the [curated_datasets](https://github.com/OpenBeta/climbing-data/tree/main/curated_datasets) 
in the climbing-data for more information.
