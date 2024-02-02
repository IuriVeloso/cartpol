import csv
import datetime
import requests
from cartpol_app.scripts.base_info import base_info
from cartpol_app.scripts.locals_update import locals_update
from cartpol_app.scripts.politics_update import post_politics
from cartpol_app.scripts.votes_update import post_votes

startTime = datetime.datetime.now()
print("\nStarted script running\n")
                    
base_info()

print("\nFinished base_info()\n")

print("\nStarted locals_update()\n")
                    
local_results = locals_update()

county_array_created = local_results[0]
section_array_created = local_results[1]

print("\nFinished locals_update()\n")

print("\nStarted post_politics()\n")

politics_array_created = post_politics(county_array_created=county_array_created)

print("\nFinished post_politics()\n")

print("\nStarted post_counties()\n")

post_votes(politics_array_created=politics_array_created, section_array_created=section_array_created)

print("\nFinished post_counties()\n")

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/update_database.py