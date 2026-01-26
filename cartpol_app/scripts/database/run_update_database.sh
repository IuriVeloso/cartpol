#!/bin/bash

# Script wrapper para executar update_database.py múltiplas vezes
# Uso: ./run_update_database.sh

SCRIPT_PATH="cartpol_app/scripts/database/update_database.py"

# Exemplo: executar duas vezes com inputs diferentes
# Primeira execução
echo "=== Executando primeira vez ==="
python3 manage.py shell -c \
  "exec(open('$SCRIPT_PATH').read())" \
  modo=l ano=2020

# Segunda execução
echo ""
echo "=== Executando segunda vez ==="
python3 manage.py shell -c \
  "exec(open('$SCRIPT_PATH').read())" \
  modo=p ano=2022

# Você pode adicionar mais execuções aqui conforme necessário
