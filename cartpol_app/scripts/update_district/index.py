import datetime

from cartpol_app.scripts.update_district.update_map_neighborhood import \
    update_map_neighborhood

URL = "http://localhost:8000/cartpol/"

timeTotalLocalResults = None
timeTotalPostPolitics = None
timeTotalPostVotes = None

startTime = datetime.datetime.now()
print(f"\nStarted script running at {startTime}\n")

update_map_neighborhood(url=URL)

print(
    f"\nFinished script running\nTotal time: \
        {datetime.datetime.now() - startTime}\n")

# python3 manage.py shell < cartpol_app/scripts/update_district/index.py
