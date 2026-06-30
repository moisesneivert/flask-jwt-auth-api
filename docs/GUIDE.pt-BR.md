# Guia de instalação e publicação

## 1. Abrir no Visual Studio Code

No PowerShell, entre na pasta do projeto:

```powershell
cd "C:\caminho\para\Flask-auth2-Auth-Api"
code .
```

## 2. Criar e ativar o ambiente virtual

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 4. Criar o arquivo de ambiente

```powershell
Copy-Item .env.example .env
```

Edite `SECRET_KEY` e `JWT_SECRET_KEY`. Para gerar valores fortes:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Execute o comando duas vezes e use um valor para cada chave.

## 5. Criar o banco

```powershell
python -m flask --app run.py db upgrade
```

## 6. Criar um administrador

```powershell
python -m flask --app run.py create-admin
```

## 7. Executar

```powershell
python run.py
```

Acesse:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/health`

## 8. Executar qualidade e testes

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Correção automática:

```powershell
python -m ruff check . --fix
python -m ruff format .
python -m pytest
```

## 9. Substituir o conteúdo do repositório existente

Copie os arquivos para a pasta que contém a pasta oculta `.git`. Não copie `.venv` nem `.env`.

```powershell
git status
git add -A
git status
git commit -m "feat: rebuild authentication API with secure JWT flow"
git push origin main
```

## 10. Renomear o repositório no GitHub

O nome recomendado é `flask-jwt-auth-api`, pois o projeto implementa JWT e não um servidor OAuth 2.0.

No GitHub:

1. Abra o repositório.
2. Entre em **Settings**.
3. Em **Repository name**, use `flask-jwt-auth-api`.
4. Clique em **Rename**.

Atualize o endereço local:

```powershell
git remote set-url origin https://github.com/moisesneivert/flask-jwt-auth-api.git
git remote -v
```
