import datetime

from cartpol_app.scripts.database.base_info import base_info
from cartpol_app.scripts.database.locals_update import locals_update
from cartpol_app.scripts.database.politics_update import post_politics
from cartpol_app.scripts.database.votes_update import post_votes

URL = "http://localhost:8000/cartpol/"

print("c(default): completo")
print("b: base_info")
print("l: localidades")
print("p: politicos")
print("v: votos")

timeTotalLocalResults = None
timeTotalPostPolitics = None
timeTotalPostVotes = None

try:
    shouldRun = input("Escolha uma opcao: ")
except:
    shouldRun = 'v'

shouldRunAll = shouldRun == None or shouldRun == 'c'
shouldRunBase = shouldRunAll or shouldRun == 'b'
shouldRunLocals = shouldRunAll or shouldRun == 'l'
shouldRunPolitics = shouldRunAll or shouldRun == 'p'
shouldRunVotes = shouldRunAll or shouldRun == 'v'

startTime = datetime.datetime.now()
year = 2024
firstRun = False
print(f"\nStarted script running at {startTime}\n")

if shouldRunBase & firstRun:
    # base_info(url=URL)

    print("\nFinished base_info()\n")

if shouldRunLocals:
    print("\nStarted locals_update()\n")

    locals_update(url=URL, year=year, firstRun=firstRun)

    timeTotalLocalResults = datetime.datetime.now() - startTime
    print(
        f"\nFinished locals_update\nTotal time: \
        {timeTotalLocalResults}\n")

if shouldRunPolitics:
    timeStartedPostPolitics = datetime.datetime.now()

    print("\nStarted post_politics()\n")

    post_politics(url=URL, year=year)

    timeTotalPostPolitics = datetime.datetime.now() - timeStartedPostPolitics
    print(
        f"\nFinished post_politics\nTotal time: \
            {timeTotalPostPolitics}\n")

if shouldRunVotes:
    timeStartedPostVotes = datetime.datetime.now()

    print("\nStarted post_votes()\n")

    post_votes(url=URL, year=year)

    timeTotalPostVotes = datetime.datetime.now() - timeStartedPostVotes
    print(
        f"\nFinished post_votes\nTotal time: \
            {timeTotalPostVotes}\n")

print(
    f"\nFinished script running\nTotal time: \
        {datetime.datetime.now() - startTime}\n")

if timeTotalLocalResults is not None:
    print(f"\nlocals_update: {timeTotalLocalResults}")

if timeTotalPostPolitics is not None:
    print(f"\npolitics_update: {timeTotalPostPolitics}")

if timeTotalPostVotes is not None:
    print(f"\npost_votes: {timeTotalPostVotes}")

# python3 manage.py shell < cartpol_app/scripts/database/update_database.py