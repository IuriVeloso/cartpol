import csv
import json
import requests

URL = "http://127.0.0.1:8000/cartpol/"

city_ids = [3, 5, 13, 14, 18]

def get_cities_results():
    for i in city_ids:
        print("Cidade: " + str(i))
        response = requests.get(URL + "results/" + str(i) + "/1/2020")
        
        for result in response.json():
            print(result)
        
        print("\n\n")
        
get_cities_results()