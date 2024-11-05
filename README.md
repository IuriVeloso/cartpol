Para rodar, usar:

source ./menv/bin/activate

python3 manage.py runserver

Para atualizar as dependencias, usar:

python3 -m pip install --upgrade pip

Para resetar a database:

python3 manage.py flush

Ao resetar a database, é necessario tambem dar os comandos de `makemigrations` and `migrate`

#Setup do programa

E necessario instalar o postgresql antes e criar um usuario apropriado para rodar o banco de dados

pip install -r ./requirements.txt 

#Subindo a plataforma

git push heroku main

Checar o link: https://devcenter.heroku.com/articles/git#deploy-your-code

Comando para converter de latin-1 para utf-8

iconv -f latin1 -t utf8 source_file.txt > target_file.txt

Exportar dados do banco como Postgres

pg_dump -Fc --no-acl --no-owner -h localhost -U cartpol_prod -d cartpol_db_name -f mydb.dump

heroku pg:backups:restore 'https://cartpol-database.s3.us-east-1.amazonaws.com/mydb.dump?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEBMaCXVzLWVhc3QtMSJIMEYCIQCppDKTmt%2BMugf5He0BzutZS9Wx0wqq%2B8o8YzcHYheSHwIhAM6Gk9iNpGTLRYS36RFQCf9RjUgqvQBIog2Jb0RsR9hoKuQCCEwQARoMODcxNTg2NDA3OTM0IgyX1z3TM3oSgOa9nPwqwQI9hU6%2BQVI0APbS0%2FrspUMLBLPMo8GKumdCoBIjfWiTXu%2Bs5jtSNnD5ZUDxMEcLue%2F6UOFs25wSxdjaN88QPOt6rHKFBluY0MCQy75Ek%2B0bgjWbQ%2Bh3jQUtCpF%2B8OX6VAp%2BJcC0%2BQtXSw5lP3Wdn6TKJb%2Fpt2w9zbZHQw%2FRtOONBwZ64BFX%2BGw352DFGC7pO%2BODlhPe2%2BRbCPq18%2F7a%2B9IDGzE1mkI26d0d%2B0xv3OBHEMmfuODHjyu3FwpDWUeQrnEMpZEyN3qWS9dRGmg65hnY8%2BbKZdNIc8EWIDHmokAqwApJg0Cya%2BIIm7FJewZ2aPPgkl2Y0EcpdTBAeTESKaA6IYuvLUEszCMqK5mRm9cIhiH0fkxITUMikSrcIzAehbEotX70k2uhKV3MfmsMLwRWB7oKN7SvT4beG8yx2xkDfVAw7L6stwY6sgIdeN0fqdv5he9m59Sy3YbK9lsBZXQGMsRgw6PFMmaTrNSd2hbHV1bjZc2sJuxfyaVGfpUJ%2FC1gqPQjwiLkn316tEAdOC9akmiD4TDzlc5OLWnah2NKH%2FgM7Uii1nTMsRwJMA2upiatPVoQvJGC%2FmVa6fxoT9%2BrCE9da5ObrcImN9s4YKFfBf4TA2EqPmcfnxBk1A278nSbaSn6D%2FMF4MVkp89H1W6%2B7Daa32M0RsQedb2RqCAdS%2FVbcUTeROMaVLTsDPyYrjHztanryWbC2W%2F2t3ROOtFSwuu%2FpJ5djgcv7gd4KddYxtDsdwkgjzTNW1W4DMvkSK0KN0YJ7sTVRfIn88g8BkQqqgI0kPpqpR3uFNZIu0PLHt850Aq3%2B9JrVgoHJzT79WcuKt6Nl2HZideF%2FaE%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240918T185229Z&X-Amz-SignedHeaders=host&X-Amz-Expires=10800&X-Amz-Credential=ASIA4V3UZEX7ASRAXHQ2%2F20240918%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=066437a2622d2cc4d45ccc0b2c265327644115ca394aede072a38ca502aebbc9' DATABASE_URL --app cartpol-api

//
Rio de Janeiro - 14
Nova Iguaçu - 18
Niterói - 5
Caxias - 13
São Gonçalo - 3
