# Visualizador Interativo do Metodo da Bisseccao

Visualizador em Python do Metodo da Bisseccao com interface interativa (Plotly).
Permite editar a equacao em tempo real pelo navegador, enviar para o servidor local
e ver o grafico e o historico de iteracoes atualizados automaticamente.

---

Sumario
- Descricao
- Recursos
- Requisitos
- Instalacao e execucao
- Como editar a equacao
- Endpoints HTTP
- Estrutura de arquivos
- Resolucao de problemas (troubleshooting)
- Contribuicao
- Licenca

---

Descricao
---------
Este repositorio fornece uma ferramenta local para visualizar o processo do
Metodo da Bisseccao. A visualizacao usa um estilo "wave" por iteracao com
marcadores para o ponto medio (xm) e controles interativos (slider, play,
zoom, reset). A equacao pode ser editada no proprio navegador e enviada ao
servidor, que gera um payload JSON que o frontend consome para atualizar o
grafico.

Recursos
--------
- Visual "wave-style" empilhado por iteracao
- Marcadores e tooltips com valores de xm, f(xm) e erro
- Slider e Play/Pause para percorrer iteracoes
- Zoom para o intervalo selecionado e reset view
- Modal no navegador para editar a expressao de f(x)
- Servidor HTTP integrado que aceita POST /set_equation
- Escrita atomica do payload JSON para evitar leituras parciais

Requisitos
----------
- Python 3.8 ou superior
- Navegador web com acesso a internet (Plotly e carregado via CDN)

Instalacao e execucao (rapido)
------------------------------
1. Clone o repositorio:

```
git clone <URL-do-repo>
cd <nome-do-repo>
```

2. (Opcional) crie e ative um ambiente virtual:

Windows PowerShell:

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```
python3 -m venv venv
source venv/bin/activate
```

3. Execute a aplicacao:

```
python interactive_bisseccao.py
```

O script:
- gera `interactive_payload.json` e `interactive_bisseccao.html`;
- inicia um servidor HTTP local (padrao: http://127.0.0.1:8000/);
- abre a pagina no navegador quando possivel;
- observa `bisseccao.py` e `user_func.py` para atualizacoes e regenera o payload.

4. Abra (se necessario) no navegador:

```
http://127.0.0.1:8000/interactive_bisseccao.html
```

Como editar a equacao
---------------------
Opcao A (recomendada - via UI):
- Na pagina, clique em "Editar equacao".
- Digite uma expressao Python em `x` (exemplos: `x**3 - x - 2`, `sin(x) - 0.5`).
- Clique em "Enviar". O servidor grava `user_func.py`, recompila e o grafico
  sera atualizado automaticamente em segundos.

Opcao B (manual):
- Edite o arquivo `user_func.py` diretamente (crie se nao existir) com o
  seguinte formato:

```
import math
from math import *

def f(x):
    return x**3 - x - 2
```

- Salve o arquivo; a aplicacao detectara a mudanca e atualizará o payload.

Endpoints HTTP
--------------
- GET /interactive_bisseccao.html  -> pagina principal
- GET /interactive_payload.json    -> payload JSON com os dados do grafico
- POST /set_equation               -> aceita JSON: { "expr": "<expressao>" }
  - escreve `user_func.py` atomico e responde {"status":"ok"}
  - exemplo curl:

```
curl -X POST -H "Content-Type: application/json" -d '{"expr":"x**3 - x - 2"}' http://127.0.0.1:8000/set_equation
```

PowerShell (Invoke-RestMethod):

```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/set_equation -Body (@{expr='x**3 - x - 2'} | ConvertTo-Json) -ContentType 'application/json'
```

Arquivos importantes
--------------------
- bisseccao.py
  - Implementacao do metodo da bisseccao. Usa `user_func.py` se existir.
- interactive_bisseccao.py
  - Gera o payload, escreve o HTML (interactive_bisseccao.html), inicia o
    servidor HTTP local e observa arquivos para atualizacoes.
- interactive_bisseccao.html
  - HTML gerado (carrega Plotly via CDN). Contem a UI e o modal para editar
    a equacao. Faz polling em interactive_payload.json para atualizacoes.
- interactive_payload.json
  - Arquivo JSON gerado pelo servidor com coordenadas e metadados do grafico.
- user_func.py
  - Arquivo gerado quando voce envia a equacao via UI; contem a funcao f(x).

Resolucao de problemas (troubleshooting)
---------------------------------------
- Pagina nao carrega / fetch bloqueado: abra a pagina via http://127.0.0.1:8000/
  em vez de file://. Execute `python interactive_bisseccao.py` para iniciar o
  servidor.
- Erro: f(a) e f(b) precisam ter sinais opostos (ValueError):
  - O metodo da bisseccao exige f(a)*f(b) < 0. Ajuste o intervalo `[a,b]`.
  - Para ajustar o intervalo padrao abra `interactive_bisseccao.py` e altere os
    parametros a0 e b0 em main(), ou altere `bisseccao.py` caso use o main.
- Grafico nao atualiza: verifique o console do navegador (F12 -> Console)
  e o terminal do servidor para possiveis erros. O servidor escreve logs quando
  recebe POST /set_equation e quando reescreve interactive_payload.json.
- Erro de javascript (ex.: showAll is not defined): atualize a pagina (F5)
  para garantir que voce esteja usando a versao atual do HTML (correcao ja
  incluida no codigo recente).

Seguranca e notas importantes
-----------------------------
- A aplicacao executa codigo Python definido pelo usuario localmente (arquivo
  user_func.py). Use com cuidado: isso e intencional para permitir flexibilidade
  em ambiente de desenvolvimento/local.
- Nao exponha o servidor local em redes publicas sem revistar seguranca.
- Plotly e carregado via CDN; se voce precisar rodar offline, podemos ajustar
  para servir a biblioteca localmente.

Contribuicao
------------
Gostaria de contribuicoes! Fluxo sugerido:

1. Fork do repositorio
2. Crie uma branch com nome descritivo: `feat/descricao` ou `fix/descricao`
3. Faça commits pequenos e claros (ex.: `feat: validar expressao antes de aceitar`)
4. Abra um Pull Request para a branch `main` com descricao do que foi alterado

Regras de commit sugeridas:
- feat: nova funcionalidade
- fix: correcao de bug
- docs: documentacao
- chore: tarefas de infraestrutura

Sugestoes de melhorias (priorizadas)
----------------------------------
1. Validacao de sintaxe da expressao enviada e teste preliminar f(a), f(b)
   para evitar chamadas que lancem excecao.
2. UI para escolher o intervalo [a, b] antes do envio da equacao.
3. Feedback visual no modal (spinner) enquanto o servidor recalcula.
4. Testes automatizados para os modulos numericos.

Licenca
-------
Este projeto pode ser distribuido sob a licenca MIT. Se quiser eu crio o
arquivo LICENSE com o texto completo da MIT.

---

Se quiser, eu ja crio o arquivo LICENSE (MIT) e um CONTRIBUTING.md basico.
Diga se quer que eu adicione isso ao repositorio agora.
