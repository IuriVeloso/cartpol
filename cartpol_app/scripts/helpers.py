def contains_duplicates_neighborhood(neighborhood_zone, neighborhood_array):
    result = True
    for neighborhood_object in neighborhood_array:
        if neighborhood_object["name"] == neighborhood_zone["name"] and neighborhood_object["county_name"] == neighborhood_zone["county_name"]:
            result = False
            break
    return result

def contains_duplicates_county(county_dict, county_array):
    result = True
    for county_object in county_array:
        if county_object["name"] == county_dict["name"]:
            result = False
            break
    return result

def contains_duplicates_electoral_zone(electoral_zone, electoral_zone_array):
    result = True
    for electoral_zone_obj in electoral_zone_array:
        if electoral_zone["identifier"] == electoral_zone_obj["identifier"]:
            result = False
            break
    return result

def contains_duplicates_political(political, political_array):
    result = True
    for political_obj in political_array:
        if political["political_id"] == political_obj["political_id"]:
            result = False
            break
    return result

def contains_duplicates_political_party(political_party, political_party_array):
    result = True
    for political_party_obj in political_party_array:
        if political_party["political_party"] == political_party_obj["name"]:
            result = False
            break
    return result
