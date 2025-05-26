#!/bin/bash

# Ativa o ambiente virtual
source ~/rasa_cotacoes_v3/rasa_env/bin/activate

# Vai até a pasta do projeto
cd ~/Downloads/rasa_cotacoes_corrigido

# Inicia SOMENTE o servidor de ações
rasa run actions
