# CartPol

CartPol é uma plataforma para gerenciamento e análise de dados, utilizando Django e PostgreSQL. Este README contém instruções para configuração, execução, atualização de dependências, manipulação do banco de dados e deploy na Heroku.

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
- [Executando o Projeto](#executando-o-projeto)
- [Atualizando Dependências](#atualizando-dependências)
- [Resetando o Banco de Dados](#resetando-o-banco-de-dados)
- [Deploy na Heroku](#deploy-na-heroku)
- [Utilitários](#utilitários)
- [Exportação e Importação de Dados](#exportação-e-importação-de-dados)
- [Cidades](#cidades)

---

## Pré-requisitos

- Python 3.x
- PostgreSQL instalado e configurado
- Git

## Instalação

Clone o repositório e instale as dependências:

```bash
git clone <url-do-repositorio>
cd cartpol
python3 -m venv menv
source ./menv/bin/activate
pip install -r requirements.txt
```

## Configuração do Banco de Dados

1. **Instale o PostgreSQL** (caso ainda não tenha):

   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Acesse o terminal do PostgreSQL:**

   ```bash
   sudo -u postgres psql
   ```

3. **Crie o banco de dados e o usuário conforme o arquivo `settings.py`:**

   ```sql
   CREATE DATABASE cartpol_db_name;
   CREATE USER cartpol_prod;
   GRANT ALL PRIVILEGES ON DATABASE cartpol_db_name TO cartpol_prod;
   ```

   Para sair do terminal do PostgreSQL, digite:
   ```
   \q
   ```

4. **Configure as variáveis de ambiente conforme necessário** (caso queira sobrescrever valores do settings.py):

   - `DB_PASSWORD`
   - `SECRET_KEY`
   - `PORT`

   Você pode definir essas variáveis no seu terminal ou em um arquivo `.env`.

---

## Executando o Projeto

Ative o ambiente virtual e rode o servidor de desenvolvimento:

```bash
source ./menv/bin/activate
python3 manage.py runserver

```

## Atualizando Dependências

Para atualizar o pip:

```bash
python3 -m pip install --upgrade pip
```

Para instalar/atualizar dependências do projeto:

```bash
pip install -r requirements.txt
```

## Resetando o Banco de Dados

Para limpar todos os dados do banco:

```bash
python3 manage.py flush
```

Após o flush, execute as migrações:

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

## Deploy na Heroku

Faça o push do código para a Heroku:

```bash
git push heroku main
```

Mais informações: [Heroku Git Deploy](https://devcenter.heroku.com/articles/git#deploy-your-code)


<!--
Comandos úteis para importação e exportação de dados:


Converter arquivos de latin-1 para utf-8:

iconv -f latin1 -t utf8 source_file.txt > target_file.txt


Exportar dados do banco PostgreSQL:

pg_dump -Fc --no-acl --no-owner -h localhost -U <usuario> -d <nome_do_banco> -f mydb.dump

heroku pg:backups:restore '{url}' DATABASE_URL --app cartpol-api

-->