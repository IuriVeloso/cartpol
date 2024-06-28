import datetime
from cartpol_app.scripts.database.base_info import base_info
from cartpol_app.scripts.database.locals_update import locals_update
from cartpol_app.scripts.database.politics_update import post_politics
from cartpol_app.scripts.database.votes_update import post_votes

env = "local"

if env == 'prod':
    URL = "https://cartpol-e2d96a7ee3e9.herokuapp.com/cartpol/"
else:
    URL = "http://localhost:8000/cartpol/"

startTime = datetime.datetime.now()
print("\nStarted script running\n")
                    
base_info(url=URL)

print("\nFinished base_info()\n")

print("\nStarted locals_update()\n")
                    
local_results = locals_update(url=URL)

timeFinishedLocalResults = datetime.datetime.now()
print(f"\nFinished locals_update\nTotal time: {timeFinishedLocalResults - startTime}\n")

county_array_created = local_results[0]
section_array_created = local_results[1]

print("\nFinished locals_update()\n")

print("\nStarted post_politics()\n")

politics_array_created = post_politics(url=URL, county_array_created=county_array_created)

timeFinishedPostPolitics = datetime.datetime.now()
print(f"\nFinished post_politics\nTotal time: {timeFinishedPostPolitics - timeFinishedLocalResults}\n")

print("\nStarted post_votes()\n")

post_votes(url=URL, politics_array_created=politics_array_created, section_array_created=section_array_created)

timeFinishedPostVotes = datetime.datetime.now()
print(f"\nFinished post_votes\nTotal time: {timeFinishedPostVotes - timeFinishedPostPolitics}\n")

# print("\nFinished post_counties()\n")

print(f"\nFinished script running\nTotal time: {datetime.datetime.now() - startTime}\n")

#python3 manage.py shell < cartpol_app/scripts/database/update_database.py