# Como rodar o Copiloto de Feedback

## Uma vez só
    pip install -r requirements.txt

## Rodar (com o front já compilado em frontend/dist)
    python -m uvicorn src.api:app --port 8000
Abra http://localhost:8000
- Visão do gerente:  http://localhost:8000/#gerente
- Visão do vendedor: http://localhost:8000/#vendedor  (abra em outra aba, de preferência com a largura de um celular)

## Se quiser mexer no front (precisa do Node.js)
    cd frontend
    npm install
    npm run build        # gera frontend/dist, que o servidor usa
    # ou, em desenvolvimento: dois terminais
    #   1) python -m uvicorn src.api:app --port 8000
    #   2) cd frontend && npm run dev   -> http://localhost:5173

## Antes de gravar a demo
Zere os feedbacks enviados: no PowerShell
    Invoke-RestMethod -Method Post http://localhost:8000/api/demo/reiniciar

## Testes
    python -m pytest
