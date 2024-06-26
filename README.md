Para rodar, usar:

source ./menv/bin/activate

python3 manage.py runserver

Para atualizar as dependencias, usar:

python3 -m pip install --upgrade pip

Para resetar a database:

python3 manage.py flush

Ao resetar a database, é necessario tambem dar os comandos de `makemigrations` and `migrate`

#Subindo a plataforma

git push heroku main

Checar o link: https://devcenter.heroku.com/articles/git#deploy-your-code

Comando para converter de latin-1 para utf-8

iconv -f latin1 -t utf8 source_file.txt > target_file.txt

//
Rio de Janeiro - 14
Nova Iguaçu - 18
Niterói - 5
Caxias - 13
São Gonçalo - 3
