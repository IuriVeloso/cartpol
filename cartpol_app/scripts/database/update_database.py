import datetime
import os
import sys

# from cartpol_app.scripts.database.base_info import base_info
from cartpol_app.scripts.database.locals_update import locals_update
from cartpol_app.scripts.database.politics_update import post_politics
from cartpol_app.scripts.database.votes_update import post_votes

URL = "http://localhost:8000/cartpol/"

timeTotalLocalResults = None
timeTotalPostPolitics = None
timeTotalPostVotes = None

# Valores padrão
shouldRun = 'c'
year = 2016

# Obtém opção e ano de variáveis globais, ambiente ou argumentos
# Uso 1: python3 manage.py shell -c \
#   "MODO='c'; ANO=2020; exec(open('script.py').read())"
# Uso 2: MODO=c ANO=2016 python3 manage.py shell < script.py
# Opções: c (completo, padrão), b (base_info), l (localidades),
#         p (politicos), v (votos)
# Ano: deve estar entre 2016 e 2024 (padrão: 2016)

# Tenta obter de variáveis globais primeiro (definidas antes do exec)
if 'MODO' in globals():
    shouldRun = globals()['MODO']
if 'ANO' in globals():
    try:
        year = int(globals()['ANO'])
    except (ValueError, TypeError):
        pass

# Tenta obter de variáveis de ambiente
if 'MODO' in os.environ:
    shouldRun = os.environ['MODO']
if 'ANO' in os.environ:
    try:
        year = int(os.environ['ANO'])
    except ValueError:
        pass

# Tenta obter de sys.argv no formato modo=c ano=2016
for arg in sys.argv[1:]:
    if arg.startswith('modo='):
        shouldRun = arg.split('=')[1]
    elif arg.startswith('ano='):
        try:
            year = int(arg.split('=')[1])
        except ValueError:
            pass

# Valida opção
if shouldRun not in ['c', 'b', 'l', 'p', 'v']:
    print(f"Opção inválida: {shouldRun}")
    print("Opções válidas: c, b, l, p, v")
    print("Usando opção padrão: c")
    shouldRun = 'c'

# Valida ano
if not (2016 <= year <= 2024):
    msg = f"Ano {year} fora do intervalo válido (2016-2024). "
    msg += "Usando padrão: 2016"
    print(msg)
    year = 2016

print(f"Opção selecionada: {shouldRun}")
print(f"Ano selecionado: {year}")

shouldRunAll = shouldRun is None or shouldRun == 'c' or shouldRun == ''
shouldRunBase = shouldRunAll or shouldRun == 'b'
shouldRunLocals = shouldRunAll or shouldRun == 'l'
shouldRunPolitics = shouldRunAll or shouldRun == 'p'
shouldRunVotes = shouldRunAll or shouldRun == 'v'

startTime = datetime.datetime.now()
print(f"\nStarted script running at {startTime}\n")

if shouldRunLocals:
    print("\nStarted locals_update()\n")

    locals_update(url=URL, year=year)

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


'''
Uso 1: Definindo variáveis antes do exec (recomendado):
python3 manage.py shell -c "MODO='c'; ANO=2020; exec(open('cartpol_app/scripts/database/update_database.py').read())"

Uso 2: Usando variáveis de ambiente:
MODO=c ANO=2016 python3 manage.py shell < \
  cartpol_app/scripts/database/update_database.py

Exemplo executando múltiplas vezes:
python3 manage.py shell -c \
  "MODO='v'; ANO=2020; \
  exec(open('cartpol_app/scripts/database/update_database.py').read())" && \
python3 manage.py shell -c \
  "MODO='v'; ANO=2020; \
  exec(open('cartpol_app/scripts/database/update_database.py').read())" && \
python3 manage.py shell -c \
  "MODO='c'; ANO=2024; \
  exec(open('cartpol_app/scripts/database/update_database.py').read())"
'''