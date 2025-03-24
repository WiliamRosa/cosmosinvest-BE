#!/bin/bash

# Criar ambiente virtual se não existir
if [ ! -d "antenv" ]; then
    python -m venv antenv
fi

# Ativar o ambiente virtual
source antenv/bin/activate

# Instalar as dependências
pip install -r requirements.txt

# Rodar a aplicação FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000