Para rodar, usar:

source ./menv/bin/activate

python3 manage.py runserver

Para atualizar as dependencias, usar:

python3 -m pip install --upgrade pip

Para resetar a database:

python3 manage.py flush

Ao resetar a database, é necessario tambem dar os comandos de `makemigrations` and `migrate`

#Setup do programa

E necessario instalar o postgresql antes

pip install -r ./requirements.txt 

#Subindo a plataforma

git push heroku main

Checar o link: https://devcenter.heroku.com/articles/git#deploy-your-code

Comando para converter de latin-1 para utf-8

iconv -f latin1 -t utf8 source_file.txt > target_file.txt

Exportar dados do banco como Postgres

pg_dump -Fc --no-acl --no-owner -h localhost -U cartpol_prod -d cartpol_db_name -f mydb.dump

heroku pg:backups:restore 'https://cartpol-database.s3.us-east-1.amazonaws.com/mydb.dump?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEFQaCXVzLWVhc3QtMSJGMEQCIG%2FbjrCPqY%2BlcATwKz3UxSgtAGrKtymvv58gseg1prNMAiA1hQMPjix1iDAsq0CKpfiGSb%2FOTD00m%2FmxtOgLFYUsRirkAgh9EAEaDDg3MTU4NjQwNzkzNCIM%2BA6rrMHQQRY1Ir%2FCKsECy%2F9TV%2FZ1TohJxQbRLrJFtDBOC6CIAhjp0DukLhzpFfIsmoIkiPsd%2B1Q6YjCOj1a1bqq3sYiH5byoHr6vdZj6K7Px2lvEDk8gdyyCnIK93YefpljZ6maKyGGVo1myluCf6o1UFveoEwFUS0ZaxgRDOSaUAWXuW6h4bYqsxfxekcpWfZnsvbk21IRFCs7Al5KWd%2BcrK1dZhDGy%2BhPcz%2BYXuAA86KEs1QzXiqus3A5esKWyp81%2FmB55R3Gt%2BQgC7ulLLHW6E7BSkxpSdRhLjI0KuZH%2FYvBAbBKrOBj96O%2FYzbPhzxentXphumtK073e%2F%2BetJ202a6pWx4hLl7mNIdES3iNHeII5HUBRqf1kXz%2B1RymBXb5lrBLDz4F5H7CS5zfGkTb4D3DYfP188t4%2BC5whY%2BnJLAZyv8XHu5w31N4XjdzLMLfEgrcGOrQCbhAoJLzHjNgjG9xjyZ24A8ng56EvHPO1QcV6B9JI03v5GIJ%2B4LoYnf7jn6etxvWnFb7faUsfmco%2FE861FOWRHinNGjfAZFx4GWWvXpcWzA3uiRrw1%2B6dAMdR6Ji3aFmgjzfcn3QaovFKy0MhlM6ABUUr7Jyewpr4ANyhc0YnLImtPRr2OH7hyPIUrz6YuC7ZveRqpKF4KlUv4HQ8dFM7IDkcsrAORx%2BFRpqO2mxgkJzhZ%2BT9B9ALIa6f9opg1bZ2%2BBPJwPaSHvOSBCxtgEvWy4bbNUkVjXjOQorhsrK0umpXUxJJuapob68WFWUtWaZAXCWi4vx%2B0W5pbtZep2eM1vk57XMW4AVcckxgIcg1Myz%2FKhGmrWLCc3R2MVx2g0LlYL5B2bYlyPdFcu609Nej90D56xI%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240910T195339Z&X-Amz-SignedHeaders=host&X-Amz-Expires=36000&X-Amz-Credential=ASIA4V3UZEX7EK3RXCH2%2F20240910%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=a6a1e73d5b5637493b8ef5b58c20b6f2a298ba5ee94f7c8a9ecaf46ee2ac2920' DATABASE_URL --app cartpol-api

//
Rio de Janeiro - 14
Nova Iguaçu - 18
Niterói - 5
Caxias - 13
São Gonçalo - 3
