import datetime

from cartpol_app.scripts.database.base_info import base_info
from cartpol_app.scripts.database.locals_update import locals_update
from cartpol_app.scripts.database.politics_update import post_politics
from cartpol_app.scripts.database.votes_update import post_votes

URL = "http://localhost:8000/cartpol/"

startTime = datetime.datetime.now()
print(f"\nStarted script running at {startTime}\n")

base_info(url=URL)

print("\nFinished base_info()\n")

print("\nStarted locals_update()\n")

section_array_created = locals_update(url=URL)

section = []

timeFinishedLocalResults = datetime.datetime.now()
print(
    f"\nFinished locals_update\nTotal time: \
    {timeFinishedLocalResults - startTime}\n")

print("\nStarted post_politics()\n")

politics_array_created = post_politics(url=URL)

timeFinishedPostPolitics = datetime.datetime.now()
print(
    f"\nFinished post_politics\nTotal time: \
        {timeFinishedPostPolitics - timeFinishedLocalResults}\n")

print("\nStarted post_votes()\n")

post_votes(url=URL, politics_array_created=politics_array_created,
           section_array_created=section_array_created)

timeFinishedPostVotes = datetime.datetime.now()
print(
    f"\nFinished post_votes\nTotal time: \
        {timeFinishedPostVotes - timeFinishedPostPolitics}\n")

# print("\nFinished post_counties()\n")

print(
    f"\nFinished script running\nTotal time: \
        {datetime.datetime.now() - startTime}\n")

# python3 manage.py shell < cartpol_app/scripts/database/update_database.py
