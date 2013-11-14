from noaahist import stn_covg, stn_flds, haversine, coords_from_zip

# load data about stations
stns = stn_covg()
flds_by_stn = stn_flds()
for _id in flds_by_stn:
    for fld in flds_by_stn[_id]:
        if flds_by_stn[_id][fld]:
            stns[_id]['flds'].append(fld)

def stns_near_lat_lon(latitude, longitude, year, N=20, id_filter=None):
    """
    latitude: float -> latitude of weather location
    longitude: negative float, coerced to negative if positive -> longitude of weather location
    year: int -> the year of desired weather data
    N: int -> number of desired results
    id_filter: function that returns station ids filtered on some condition

    displays information about the N closest stations to the given coordinates
    """
    latitude = float(latitude)
    longitude = float(longitude)
    if longitude > 0.:
        longitude = -1. * longitude
    lines = [" ".join(['   ', "Station ID".ljust(12), "Station Name".ljust(30), "    ", "Dist. (miles)"]) + "\n"]
    def show_stn(stn_id, rank):
        d = stns[stn_id]
        info_str = " ".join([(str(rank)+".").ljust(3),
                             stn_id.ljust(12),
                             stns[stn_id]['name'].ljust(30),
                             stns[stn_id]['state'].ljust(4),
                             str(round(haversine(latitude, longitude, stns[stn_id]['lat'], stns[stn_id]['lon']), 1))]) + "\n"
        return info_str
    stn_ids = [_id for _id in stns if int(stns[_id]['sd'].year) <= year and int(stns[_id]['ed'].year) >= year]
    # optionally filter station ids
    if id_filter:
        stn_ids = id_filter(stn_ids)
    _ids = sorted(stn_ids, key=lambda _id: haversine(latitude, longitude, stns[_id]['lat'], stns[_id]['lon']))[:N]
    lines += [show_stn(_id, j) for j, _id in enumerate(_ids)]
    if len(lines) > 1:
        print "".join(lines)
    else:
        print "No stations were found that matched these criteria."

def stns_near_zip(zip, year, N=20, id_filter=None):
    try:
        (lat, lon) = coords_from_zip(zip)
        stns_near_lat_lon(lat, lon, year, N, id_filter)
    except ImportError:
        print "pyzipcode is not available -> try using stns_near_lat_lon()"

def stns_with_fld(fld, latitude, longitude, year, N=20):
    valid_flds = ['TEMP','MIN','MAX','DEWP','DIR','SPD','GUS','PCP01','PCPXX','PCP06','PCP24','SD','SKC',
                  'CLG','L','M','H','AW1','AW2','AW3','AW4','MW1','MW2','MW3','MW4','SLP','STP','ALT','VSB','W',]
    assert fld in valid_flds, "the fld argument is not among the valid fields: %s" % ", ".join(valid_flds)
    def filter_ids(stn_ids):
        return [x for x in stn_ids if fld in stns[x]['flds']]
    stns_near_lat_lon(latitude, longitude, year, N, filter_ids)
    
def stns_with_fld_zip(fld, zip, year, N=20):
    try:
        (lat, lon) = coords_from_zip(zip)
        stns_with_fld(fld, lat, lon, year, N)
    except ImportError:
        print "pyzipcode is not available -> try using stns_near_lat_lon()"

if __name__ == "__main__":
    print "This module is for interactive exploration."
    print "Find weather stations near a location, optionally requesting that a certain field is likely to be present."
    print "There are no guarantees that the data for any field will exist.  Data observations are sparse in many cases."
    print """Example:
 >>> from explore_stations import *
 >>> stns_with_fld("TEMP", 38.9, -77.0, 2013)"""
