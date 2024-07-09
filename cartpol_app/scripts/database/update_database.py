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

try:
    shouldRun = input("Escolha uma opcao: ")
except:
    shouldRun = 'c'

shouldRunAll = shouldRun == None or shouldRun == 'c'
shouldRunBase = shouldRunAll or shouldRun == 'b'
shouldRunLocals = shouldRunAll or shouldRun == 'l'
shouldRunPolitics = shouldRunAll or shouldRun == 'p'
shouldRunVotes = shouldRunAll or shouldRun == 'v'

startTime = datetime.datetime.now()
print(f"\nStarted script running at {startTime}\n")

if shouldRunBase:
    base_info(url=URL)

    print("\nFinished base_info()\n")

if shouldRunLocals:
    print("\nStarted locals_update()\n")

    locals_update(url=URL)

    section = []

    timeFinishedLocalResults = datetime.datetime.now()
    print(
        f"\nFinished locals_update\nTotal time: \
        {timeFinishedLocalResults - startTime}\n")

if shouldRunPolitics:
    timeStartedPostPolitics = datetime.datetime.now()
    
    print("\nStarted post_politics()\n")

    post_politics(url=URL)

    timeFinishedPostPolitics = datetime.datetime.now()
    print(
        f"\nFinished post_politics\nTotal time: \
            {timeFinishedPostPolitics - timeStartedPostPolitics}\n")

if shouldRunVotes:
    timeStartedPostVotes = datetime.datetime.now()
    
    print("\nStarted post_votes()\n")

    post_votes(url=URL)

    timeFinishedPostVotes = datetime.datetime.now()
    print(
        f"\nFinished post_votes\nTotal time: \
            {timeFinishedPostVotes - timeStartedPostVotes}\n")

print(
    f"\nFinished script running\nTotal time: \
        {datetime.datetime.now() - startTime}\n")

# python3 manage.py shell < cartpol_app/scripts/database/update_database.py
