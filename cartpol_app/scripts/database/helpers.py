def contains_duplicates_neighborhood(neighborhood_name, neighborhood_county, neighborhood_array):
    result = True
    for neighborhood_object in neighborhood_array:
        if neighborhood_object["name"] == neighborhood_name and neighborhood_object["county_name"] == neighborhood_county:
            result = False
            break
    return result

def contains_duplicates_county(county_name, county_array):
    result = True
    for county_object in county_array:
        if county_object["name"] == county_name:
            result = False
            break
    return result

def contains_duplicates_electoral_zone(electoral_zone_identifier, electoral_zone_state, electoral_zone_county, electoral_zone_array):
    result = True
    for electoral_zone_obj in electoral_zone_array:
        if electoral_zone_identifier == electoral_zone_obj["identifier"]\
            and electoral_zone_state == electoral_zone_obj["state"]\
            and electoral_zone_county == electoral_zone_obj["county"]:
            result = False
            break
    return result

def contains_duplicates_state(state_name, state_array):
    result = True
    for state_obj in state_array:
        if state_name == state_obj["name"]:
            result = False
            break
    return result

def contains_duplicates_political(political, political_array):
    result = True
    for political_obj in political_array:
        if political["political_id"] == political_obj["political_id"] and political["county_id"] == political_obj["county_id"]:
            result = False
            break
    return result

def contains_duplicates_political_party(political_party_name, political_party_array):
    result = True
    for political_party_obj in political_party_array:
        if political_party_name == political_party_obj["name"]:
            result = False
            break
    return result
