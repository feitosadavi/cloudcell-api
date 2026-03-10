"""
CRUD completo do estoque via API REST.

Endpoints:
  POST   /admin/estoque/                  Criar produto
  GET    /admin/estoque/                  Listar (paginado, filtro disponíveis)
  GET    /admin/estoque/buscar            Busca fuzzy
  GET    /admin/estoque/{id}              Obter por ID
  PUT    /admin/estoque/{id}              Substituição completa
  PATCH  /admin/estoque/{id}             Atualização parcial
  PATCH  /admin/estoque/{id}/estoque     Ajustar quantidade (+/-)
  DELETE /admin/estoque/{id}             Soft delete (desativa)
  DELETE /admin/estoque/{id}/permanente  Hard delete
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .database import (
    ajustar_estoque,
    atualizar_produto,
    buscar_produtos,
    deletar_produto,
    desativar_produto,
    inserir_produto,
    listar_produtos,
    obter_produto,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/estoque", tags=["Estoque"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProdutoIn(BaseModel):
    nome: str                          = Field(..., examples=["IPHONE 13"])
    armazenamento: Optional[str]       = Field(None, examples=["128GB"])
    imei: Optional[str]                = Field(None, examples=["356808582277873"])
    cor: Optional[str]                 = Field(None, examples=["PRETO"])
    tipo: Optional[str]                = Field(None, examples=["SEMINOVO"])
    valor: Optional[float]             = Field(None, examples=[2150.00])
    bateria: Optional[str]             = Field(None, examples=["89%"])
    estado: Optional[str]              = Field(None, examples=["SEMINOVO"])
    qtd: int                           = Field(1, ge=0)


class ProdutoPatch(BaseModel):
    nome: Optional[str]                = None
    armazenamento: Optional[str]       = None
    imei: Optional[str]                = None
    cor: Optional[str]                 = None
    tipo: Optional[str]                = None
    valor: Optional[float]             = None
    bateria: Optional[str]             = None
    estado: Optional[str]              = None
    qtd: Optional[int]                 = Field(None, ge=0)
    ativo: Optional[int]               = Field(None, ge=0, le=1)


class AjusteEstoque(BaseModel):
    delta: int = Field(..., description="Positivo para entrada, negativo para saída", examples=[1, -1])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _404(produto_id: int):
    raise HTTPException(status_code=404, detail=f"Produto {produto_id} não encontrado.")


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201, summary="Criar produto")
def criar_produto(produto: ProdutoIn):
    try:
        pid = inserir_produto(produto.model_dump())
        return {"id": pid, "status": "criado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── READ ──────────────────────────────────────────────────────────────────────

@router.get("/", summary="Listar estoque (paginado)")
def listar(
    apenas_disponiveis: bool = Query(True, description="Apenas com qtd > 0 e ativos"),
    pagina: int             = Query(1, ge=1),
    por_pagina: int         = Query(50, ge=1, le=200),
):
    return listar_produtos(apenas_disponiveis, pagina, por_pagina)


@router.get("/buscar", summary="Busca fuzzy por nome/modelo/cor/etc")
def buscar(
    q: str             = Query(..., description="Ex: iphone 13 preto 128gb"),
    limite: int        = Query(5, ge=1, le=50),
    score_minimo: int  = Query(40, ge=0, le=100),
):
    return buscar_produtos(q, limite=limite, score_minimo=score_minimo)


@router.get("/{produto_id}", summary="Obter produto por ID")
def obter(produto_id: int):
    p = obter_produto(produto_id)
    if not p:
        _404(produto_id)
    return p


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.put("/{produto_id}", summary="Substituir produto completo (PUT)")
def substituir_produto(produto_id: int, produto: ProdutoIn):
    if not obter_produto(produto_id):
        _404(produto_id)
    dados = produto.model_dump()
    dados["ativo"] = 1
    result = atualizar_produto(produto_id, dados)
    if not result:
        _404(produto_id)
    return result


@router.patch("/{produto_id}", summary="Atualizar campos parcialmente (PATCH)")
def atualizar_parcial(produto_id: int, produto: ProdutoPatch):
    if not obter_produto(produto_id):
        _404(produto_id)
    dados = {k: v for k, v in produto.model_dump().items() if v is not None}
    result = atualizar_produto(produto_id, dados)
    if not result:
        _404(produto_id)
    return result


@router.patch("/{produto_id}/estoque", summary="Ajustar quantidade em estoque")
def ajustar(produto_id: int, ajuste: AjusteEstoque):
    result = ajustar_estoque(produto_id, ajuste.delta)
    if not result:
        _404(produto_id)
    return {
        "id": produto_id,
        "qtd_anterior": result["qtd"] - ajuste.delta if result["qtd"] > 0 else 0,
        "qtd_atual": result["qtd"],
        "delta": ajuste.delta,
    }


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete("/{produto_id}", summary="Desativar produto (soft delete)")
def desativar(produto_id: int):
    result = desativar_produto(produto_id)
    if not result:
        _404(produto_id)
    return {"id": produto_id, "status": "desativado", "ativo": 0, "qtd": 0}


@router.delete("/{produto_id}/permanente", summary="Deletar produto permanentemente (hard delete)")
def deletar_permanente(produto_id: int):
    if not obter_produto(produto_id):
        _404(produto_id)
    ok = deletar_produto(produto_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Erro ao deletar.")
    return {"id": produto_id, "status": "deletado permanentemente"}