#!/bin/bash

# Caminho para o ambiente virtual
VENV_DIR="/home/site/wwwroot/antenv"

# Criar ambiente virtual se não existir
if [ ! -d "$VENV_DIR" ]; then
    python -m venv $VENV_DIR
fi

# Ativar o ambiente virtual
source $VENV_DIR/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Rodar a aplicação FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
