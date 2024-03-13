from fastapi import FastAPI, HTTPException
import httpx
import re
import json

app = FastAPI()

cep_cache = {}

def validar_cep(cep: str) -> bool:
    return re.fullmatch(r"\d{5}-?\d{3}", cep) is not None

async def consultar_cep_externo(cep: str) -> dict:
    url = f"https://viacep.com.br/ws/{cep}/json/"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=404, detail="CEP não encontrado")

@app.get("/cep/{cep}")
async def buscar_cep(cep: str):
    cep = cep.replace("-", "")
    
    if not validar_cep(cep):
        raise HTTPException(status_code=400, detail="Formato de CEP inválido")
    
    if cep in cep_cache:
        return {"data": cep_cache[cep], "cache": True}
    
    dados_cep = await consultar_cep_externo(cep)
    
    cep_cache[cep] = dados_cep

    _save_cep(dados_cep)

    return {"data": dados_cep, "cache": False}
    

@app.get("/backup/{cep}")
async def consultar_cache(cep: str):
    cep = cep.replace("-", "")
    
    if cep in cep_cache:
        return {"data": cep_cache[cep]}
    else:
        raise HTTPException(status_code=404, detail="CEP não encontrado no cache")

@app.get("/backup/")
async def consultar_todo_backup():
    return get_all_cep()

def _load_backup() -> dict :
    try:
        with open("cepbackup_db.txt", "r") as file:
            return [json.loads(line) for line in file]
    except FileNotFoundError:
        return {}

def _save_cep(cep_data: {}):
    with open("cepbackup_db.txt", "a") as file:
        cep_data = json.dumps(cep_data)
        file.write(f"{cep_data}\n")

def get_all_cep() -> {}:
    return _load_backup()