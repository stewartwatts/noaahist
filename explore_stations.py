from noaahist import stn_covg, stn_flds, haversine, coords_from_zip, datestr_to_dt

# load data about stations
stns = stn_covg()
flds_by_stn = stn_flds()
for _id in flds_by_stn:
    for fld in flds_by_stn[_id]:
        if flds_by_stn[_id][fld]:
            stns[_id]['flds'].append(fld)

def view_stns_near_lat_lon(latitude, longitude, year, N=20):
    """
    latitude: float -> latitude of weather location
    longitude: negative float, coerced to negative if positive -> longitude of weather location
    year: int -> the year of desired weather data
    N: int -> number of desired results

    displays information about the N closest stations
    """
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
    _ids = sorted(stn_ids, key=lambda _id: haversine(latitude, longitude, stns[_id]['lat'], stns[_id]['lon']))[:N]
    lines += [show_stn(_id, j) for j, _id in enumerate(_ids)]
    print "".join(lines)

def view_stns_near_zip(zip, year, N=20):
    try:
        view_stns_near_lat_lon(*coords_from_zip(zip), year, N)
    except ImportError:
        print "pyzipcode is not available -> try using view_stns_near_lat_lon()"

def view_stns_with_fld(fld, latitude, longitude, year, N=20):
    assert fld in ['TEMP','MIN','MAX','DEWP','DIR','SPD','GUS','PCP01','PCPXX','PCP06','PCP24','SD','SKC',
                   'CLG','L','M','H','AW1','AW2','AW3','AW4','MW1','MW2','MW3','MW4','SLP','STP','ALT','VSB','W',]
    
