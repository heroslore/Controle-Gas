#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produtividade MODIS (MOD17, Coleção 6.1) por bioma na Bahia via Google Earth Engine.

Substitui o fluxo manual (Earthdata + MRT + ArcGIS) da metodologia de
Benfica et al. (2022) por um pipeline reprodutível em Python. Dois modos:

  --produto anual   MODIS/061/MOD17A3HGF, banda Npp (NPP anual, kg C/m² x 0,0001)
                    -> CSV: ano, bioma, npp_g_c_m2
  --produto mensal  MODIS/061/MOD17A2HGF, banda PsnNet (fotossíntese líquida
                    8-dias, kg C/m² x 0,0001) somada por mês
                    -> CSV: ano, mes, bioma, psn_g_c_m2
                    (é o formato da série histórica 2001-2020 "dados_graficos_Benfica")

Etapas: autentica no Earth Engine; lista os anos/datas disponíveis; recorta os
biomas Mata Atlântica, Cerrado e Caatinga pelo limite da Bahia (shapefiles
oficiais do IBGE, baixados automaticamente se pedido); calcula a média
espacial por bioma; grava CSV; reporta erros de forma explícita.

Uso típico (primeira vez):

    python npp_modis_gee.py --project MEU-PROJETO-GEE --baixar-ibge dados_ibge

Depois, apenas:

    python npp_modis_gee.py --project MEU-PROJETO-GEE --produto mensal \
        --biomas dados_ibge/lm_bioma_250.shp --bahia dados_ibge/BA_UF_2022.shp

Veja README.md para instalação, autenticação e opções.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import json
import os
import sys
import textwrap
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ----------------------------------------------------------------------------
# Produtos MOD17 v6.1 no catálogo do GEE
# ----------------------------------------------------------------------------

PRODUTOS = {
    "anual": {
        "colecao": "MODIS/061/MOD17A3HGF",
        "banda": "Npp",
        "banda_qc": "Npp_QC",          # % de entradas 8-dias preenchidas (0-100)
        "valido": (-30000, 32700),     # int16; 32761-32767 são códigos de fill
        "coluna": "npp_g_c_m2",
    },
    "mensal": {
        "colecao": "MODIS/061/MOD17A2HGF",
        "banda": "PsnNet",
        "banda_qc": None,              # Psn_QC é bitmask; não filtrado aqui
        "valido": (-30000, 30000),
        "coluna": "psn_g_c_m2",
    },
}

# Fator de escala 0,0001 kg C/m². 1 kg C/m² = 1000 g C/m²
#  ->  g C/m² = DN * 0,0001 * 1000 = DN * 0,1  (o mesmo 0,1 do fluxo MRT/ArcGIS).
FATOR_ESCALA_KG = 0.0001
KG_PARA_G = 1000.0

BIOMAS_PADRAO = ("Mata Atlântica", "Cerrado", "Caatinga")

# Fontes oficiais IBGE (biomas 1:250.000, versão 2019; malha estadual 2022).
URL_IBGE_BIOMAS = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "biomas/vetores/Biomas_250mil.zip"
)
URL_IBGE_BAHIA = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2022/UFs/BA/BA_UF_2022.zip"
)
ARQ_IBGE_BIOMAS = "lm_bioma_250.shp"
ARQ_IBGE_BAHIA = "BA_UF_2022.shp"

# Limite administrativo de reserva (se o usuário não fornecer o shapefile da
# Bahia): FAO GAUL 2015, nível 1, disponível no catálogo do GEE.
GAUL_ADM1 = "FAO/GAUL/2015/level1"


# ----------------------------------------------------------------------------
# Utilidades de log e erro
# ----------------------------------------------------------------------------

class ErroPipeline(Exception):
    """Erro esperado, com mensagem pronta para o usuário."""


def log(msg: str = "") -> None:
    print(msg, file=sys.stderr, flush=True)


def falhar(msg: str, codigo: int = 1) -> None:
    log("\nERRO: " + msg)
    sys.exit(codigo)


# ----------------------------------------------------------------------------
# 1. Autenticação / inicialização do Earth Engine
# ----------------------------------------------------------------------------

def importar_ee():
    try:
        import ee  # noqa: WPS433
    except ImportError:
        raise ErroPipeline(
            "O pacote 'earthengine-api' não está instalado.\n"
            "Instale com:  pip install -r requirements.txt"
        )
    except BaseException as exc:  # noqa: BLE001  (ex.: cryptography quebrada)
        raise ErroPipeline(
            "O pacote 'earthengine-api' está instalado mas falhou ao importar "
            f"({type(exc).__name__}: {exc}).\n"
            "Geralmente é dependência quebrada; tente:\n"
            "  pip install --upgrade --force-reinstall cffi cryptography "
            "google-auth earthengine-api"
        )
    return ee


def _autenticar(ee, auth_mode: Optional[str]) -> None:
    """ee.Authenticate com fallback: se o modo padrão exigir gcloud e ele não
    existir, usa o modo 'notebook' (imprime um link e pede o código)."""
    try:
        ee.Authenticate(auth_mode=auth_mode) if auth_mode else ee.Authenticate()
    except Exception as exc:  # noqa: BLE001
        if "gcloud" in str(exc).lower() and auth_mode in (None, "gcloud"):
            log("gcloud não encontrado; tentando autenticação modo 'notebook' "
                "(abra o link mostrado e cole o código).")
            ee.Authenticate(auth_mode="notebook")
        else:
            raise


def inicializar_ee(project: Optional[str], forcar_auth: bool,
                   service_account: Optional[str], chave_json: Optional[str],
                   auth_mode: Optional[str] = None):
    """Inicializa o EE. Tenta credenciais salvas; se falhar, abre o fluxo de
    autenticação interativo. Erros comuns viram mensagens explicativas."""
    ee = importar_ee()

    if not project:
        raise ErroPipeline(
            "Informe o ID do projeto Google Cloud registrado no Earth Engine "
            "com --project (ou variável de ambiente EE_PROJECT).\n"
            "Como criar/registrar: veja a seção 'Configuração do projeto GEE' "
            "no README.md."
        )

    # Conta de serviço (execução sem navegador, ex.: servidor/cluster).
    if service_account or chave_json:
        if not (service_account and chave_json):
            raise ErroPipeline(
                "Para usar conta de serviço informe AMBOS: "
                "--service-account EMAIL e --chave-json ARQUIVO.json"
            )
        if not Path(chave_json).is_file():
            raise ErroPipeline(f"Arquivo de chave não encontrado: {chave_json}")
        try:
            cred = ee.ServiceAccountCredentials(service_account, chave_json)
            ee.Initialize(credentials=cred, project=project)
            log(f"Earth Engine inicializado com conta de serviço ({project}).")
            return ee
        except Exception as exc:  # noqa: BLE001
            raise ErroPipeline(
                "Falha ao inicializar com conta de serviço.\n"
                f"Detalhe: {exc}\n"
                "Verifique se a conta de serviço foi registrada em "
                "https://code.earthengine.google.com/register e se o projeto "
                "tem a API Earth Engine habilitada."
            ) from exc

    def _init():
        ee.Initialize(project=project)

    try:
        if forcar_auth:
            raise RuntimeError("autenticação forçada por --autenticar")
        _init()
    except Exception as primeiro_erro:  # noqa: BLE001
        log("Credenciais do Earth Engine ausentes/inválidas "
            f"({type(primeiro_erro).__name__}). Abrindo autenticação...")
        try:
            _autenticar(ee, auth_mode)
            _init()
        except Exception as exc:  # noqa: BLE001
            texto = str(exc)
            baixo = texto.lower()
            dica = ""
            if "not registered" in baixo or "not signed up" in baixo:
                dica = ("\nSua conta Google ou o projeto ainda não estão "
                        "registrados no Earth Engine: "
                        "https://code.earthengine.google.com/register")
            elif "permission" in baixo or "403" in texto:
                dica = ("\nO projeto existe mas você não tem permissão nele, "
                        "ou a API 'Earth Engine' não está habilitada no projeto "
                        "(console.cloud.google.com > APIs e serviços).")
            elif "project" in baixo and "not found" in baixo:
                dica = f"\nO projeto '{project}' não foi encontrado. Confira o ID."
            raise ErroPipeline(
                "Não foi possível autenticar/inicializar o Earth Engine.\n"
                f"Detalhe: {texto}{dica}\n"
                "Tente executar manualmente no terminal:  earthengine authenticate"
            ) from exc

    log(f"Earth Engine inicializado (projeto: {project}).")
    return ee


# ----------------------------------------------------------------------------
# 2. Datas disponíveis na coleção
# ----------------------------------------------------------------------------

def datas_disponiveis(ee, colecao: str) -> List[dt.date]:
    try:
        tempos = ee.ImageCollection(colecao).aggregate_array(
            "system:time_start").getInfo()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(
            f"Falha ao consultar a coleção {colecao}.\nDetalhe: {exc}\n"
            "Confira o id da coleção (--colecao) e se o projeto tem acesso ao "
            "catálogo público."
        ) from exc
    if not tempos:
        raise ErroPipeline(f"A coleção {colecao} retornou vazia.")
    return sorted({dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date()
                   for t in tempos})


def relatar_disponibilidade(datas: Sequence[dt.date], produto: str,
                            colecao: str) -> Dict[int, List[dt.date]]:
    por_ano: Dict[int, List[dt.date]] = {}
    for d in datas:
        por_ano.setdefault(d.year, []).append(d)
    anos = sorted(por_ano)
    log(f"\n{colecao}: {len(datas)} imagens, {anos[0]} a {anos[-1]}.")
    if produto == "anual":
        log(f"ÚLTIMO ANO DISPONÍVEL (NPP anual): {anos[-1]}")
    else:
        ultimo = anos[-1]
        n = len(por_ano[ultimo])
        log(f"Última composição 8-dias: {datas[-1].isoformat()}  "
            f"({n} de 46 composições em {ultimo})")
        completo = ultimo if n >= 46 else (ultimo - 1 if ultimo - 1 in por_ano else None)
        log(f"ÚLTIMO ANO COMPLETO (46 composições): {completo}")
    return por_ano


def resolver_intervalo(por_ano: Dict[int, List[dt.date]], inicio: int,
                       fim: Optional[int]) -> List[int]:
    anos_ok = sorted(por_ano)
    ultimo = anos_ok[-1]
    if fim is None:
        fim = ultimo
    if inicio > fim:
        raise ErroPipeline(f"--inicio ({inicio}) é maior que --fim ({fim}).")
    pedidos = list(range(inicio, fim + 1))
    faltando = [a for a in pedidos if a not in por_ano]
    if faltando:
        log("AVISO: anos solicitados sem dado na coleção e que serão "
            f"ignorados: {faltando} (último ano disponível: {ultimo}).")
    validos = [a for a in pedidos if a in por_ano]
    if not validos:
        raise ErroPipeline(
            f"Nenhum dos anos pedidos ({inicio}-{fim}) existe na coleção. "
            f"Anos disponíveis: {anos_ok[0]}-{ultimo}."
        )
    return validos


# ----------------------------------------------------------------------------
# 3. Limites dos biomas na Bahia
# ----------------------------------------------------------------------------

def baixar_ibge(destino: Path) -> Tuple[Path, Path]:
    """Baixa e extrai os shapefiles do IBGE (biomas e limite da Bahia)."""
    destino.mkdir(parents=True, exist_ok=True)
    resultados = []
    for url, alvo in ((URL_IBGE_BIOMAS, ARQ_IBGE_BIOMAS),
                      (URL_IBGE_BAHIA, ARQ_IBGE_BAHIA)):
        shp = destino / alvo
        if shp.is_file():
            log(f"Já existe, pulando download: {shp}")
            resultados.append(shp)
            continue
        zip_path = destino / url.rsplit("/", 1)[-1]
        log(f"Baixando {url} ...")
        try:
            urllib.request.urlretrieve(url, zip_path)  # noqa: S310
        except Exception as exc:  # noqa: BLE001
            raise ErroPipeline(
                f"Falha ao baixar {url}\nDetalhe: {exc}\n"
                "Baixe manualmente no navegador, extraia e informe os caminhos "
                "com --biomas e --bahia."
            ) from exc
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(destino)
        if not shp.is_file():
            raise ErroPipeline(
                f"O arquivo {alvo} não foi encontrado após extrair {zip_path}. "
                "O IBGE pode ter renomeado o conteúdo; informe o .shp manualmente."
            )
        log(f"Extraído: {shp}")
        resultados.append(shp)
    return resultados[0], resultados[1]


def importar_geo():
    try:
        import geopandas as gpd
        import shapely
    except ImportError:
        raise ErroPipeline(
            "Os pacotes 'geopandas' e 'shapely' são necessários para ler "
            "shapefiles locais.\nInstale com:  pip install -r requirements.txt"
        )
    return gpd, shapely


def ler_vetor(caminho: str, gpd):
    p = Path(caminho)
    if not p.exists():
        raise ErroPipeline(
            f"Arquivo vetorial não encontrado: {caminho}\n"
            "Se você não tem os shapefiles, use --baixar-ibge PASTA para obter "
            "os limites oficiais do IBGE automaticamente."
        )
    try:
        gdf = gpd.read_file(p)
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(f"Falha ao ler {caminho}: {exc}") from exc
    if gdf.empty:
        raise ErroPipeline(f"O arquivo {caminho} não contém feições.")
    if gdf.crs is None:
        log(f"AVISO: {caminho} sem CRS definido; assumindo EPSG:4674 (SIRGAS 2000).")
        gdf = gdf.set_crs(4674)
    return gdf.to_crs(4326)


def _uniao(geoseries):
    return geoseries.union_all() if hasattr(geoseries, "union_all") \
        else geoseries.unary_union


def _para_ee_geometry(ee, geom, tolerancia: float, shapely):
    """Converte geometria shapely (EPSG:4326) em ee.Geometry planar."""
    if tolerancia > 0:
        geom = geom.simplify(tolerancia, preserve_topology=True)
    geom = shapely.make_valid(geom)
    if geom.geom_type == "GeometryCollection":
        # Interseções podem deixar linhas/pontos residuais; fica só o polígono.
        partes = [g for g in shapely.get_parts(geom)
                  if g.geom_type in ("Polygon", "MultiPolygon")]
        if not partes:
            raise ErroPipeline("A interseção bioma × Bahia não gerou polígonos.")
        geom = shapely.union_all(partes)
    gj = json.loads(shapely.to_geojson(geom))
    if gj["type"] not in ("Polygon", "MultiPolygon"):
        raise ErroPipeline(f"Geometria inesperada ({gj['type']}); esperado polígono.")
    tamanho_mb = len(json.dumps(gj)) / 1e6
    if tamanho_mb > 8:
        raise ErroPipeline(
            f"Geometria com {tamanho_mb:.1f} MB excede o limite de requisição "
            "do GEE (10 MB). Aumente --tolerancia (ex.: 0.001) ou envie o "
            "shapefile como asset do GEE e use --biomas <id_do_asset>."
        )
    return ee.Geometry(gj, "EPSG:4326", False), shapely.get_num_coordinates(geom)


def limite_bahia_gaul_shapely(ee, shapely):
    fc = ee.FeatureCollection(GAUL_ADM1).filter(
        ee.Filter.And(ee.Filter.eq("ADM0_NAME", "Brazil"),
                      ee.Filter.eq("ADM1_NAME", "Bahia")))
    try:
        info = fc.geometry().getInfo()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(
            f"Falha ao obter o limite da Bahia em {GAUL_ADM1}: {exc}") from exc
    return shapely.geometry.shape(info)


def biomas_locais(ee, caminho_biomas: str, caminho_bahia: Optional[str],
                  campo: str, nomes: Sequence[str], tolerancia: float
                  ) -> Dict[str, "ee.Geometry"]:
    """Lê shapefile de biomas, recorta pela Bahia e devolve {nome: ee.Geometry}."""
    gpd, shapely = importar_geo()
    biomas = ler_vetor(caminho_biomas, gpd)
    if campo not in biomas.columns:
        raise ErroPipeline(
            f"O campo '{campo}' não existe em {caminho_biomas}. "
            f"Campos disponíveis: {[c for c in biomas.columns if c != 'geometry']}. "
            "Use --campo-bioma para indicar o campo com o nome do bioma."
        )

    if caminho_bahia:
        limite_ba = _uniao(ler_vetor(caminho_bahia, gpd).geometry)
        origem_ba = caminho_bahia
    else:
        log("Limite da Bahia não informado (--bahia); usando FAO GAUL 2015 do GEE.")
        limite_ba = limite_bahia_gaul_shapely(ee, shapely)
        origem_ba = GAUL_ADM1

    resultado: Dict[str, "ee.Geometry"] = {}
    faltantes = []
    for nome in nomes:
        sel = biomas[biomas[campo].astype(str).str.strip().str.casefold()
                     == nome.strip().casefold()]
        if sel.empty:
            faltantes.append(nome)
            continue
        geom = _uniao(sel.geometry).intersection(limite_ba)
        if geom.is_empty:
            raise ErroPipeline(
                f"O bioma '{nome}' não intersecta o limite da Bahia ({origem_ba})."
            )
        area_km2 = float(
            gpd.GeoSeries([geom], crs=4326).to_crs(5880).area.iloc[0] / 1e6)
        ee_geom, nvert = _para_ee_geometry(ee, geom, tolerancia, shapely)
        log(f"  {nome}: {area_km2:,.0f} km² na Bahia, {nvert} vértices enviados ao GEE")
        resultado[nome] = ee_geom

    if faltantes:
        disponiveis = sorted(biomas[campo].astype(str).unique())
        raise ErroPipeline(
            f"Bioma(s) não encontrado(s) no campo '{campo}': {faltantes}.\n"
            f"Valores existentes: {disponiveis}.\n"
            "Ajuste --biomas-nomes (ou --campo-bioma) para casar com o arquivo."
        )
    return resultado


def limite_bahia_ee(ee, caminho_bahia: Optional[str], tolerancia: float):
    if caminho_bahia:
        gpd, shapely = importar_geo()
        geom = _uniao(ler_vetor(caminho_bahia, gpd).geometry)
        return _para_ee_geometry(ee, geom, tolerancia, shapely)[0]
    return ee.FeatureCollection(GAUL_ADM1).filter(
        ee.Filter.And(ee.Filter.eq("ADM0_NAME", "Brazil"),
                      ee.Filter.eq("ADM1_NAME", "Bahia"))).geometry()


def biomas_asset(ee, asset_id: str, caminho_bahia: Optional[str], campo: str,
                 nomes: Sequence[str], tolerancia: float) -> Dict[str, "ee.Geometry"]:
    """Biomas a partir de um asset (FeatureCollection) já enviado ao GEE."""
    try:
        fc = ee.FeatureCollection(asset_id)
        valores = fc.aggregate_array(campo).distinct().getInfo()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(
            f"Não foi possível abrir o asset '{asset_id}' (campo '{campo}').\n"
            f"Detalhe: {exc}"
        ) from exc
    if not valores:
        raise ErroPipeline(
            f"O asset {asset_id} não possui o campo '{campo}' ou está vazio. "
            "Use --campo-bioma para indicar o campo correto."
        )
    limite = limite_bahia_ee(ee, caminho_bahia, tolerancia)
    resultado = {}
    faltantes = []
    for nome in nomes:
        casado = [v for v in valores if str(v).strip().casefold() == nome.casefold()]
        if not casado:
            faltantes.append(nome)
            continue
        geom = fc.filter(ee.Filter.eq(campo, casado[0])).geometry()
        resultado[nome] = geom.intersection(limite, 100)
        log(f"  {nome}: asset '{casado[0]}' recortado pela Bahia (no GEE)")
    if faltantes:
        raise ErroPipeline(
            f"Bioma(s) ausente(s) no asset: {faltantes}. Valores: {valores}"
        )
    return resultado


# ----------------------------------------------------------------------------
# 4. Imagens por período (ano ou mês), em g C/m²
# ----------------------------------------------------------------------------

def _mascarar_escalar(ee, img, banda: str, valido: Tuple[int, int],
                      banda_qc: Optional[str], qc_max: Optional[int]):
    b = img.select(banda)
    mascara = b.gte(valido[0]).And(b.lte(valido[1]))
    if banda_qc and qc_max is not None:
        mascara = mascara.And(img.select(banda_qc).lte(qc_max))
    return b.updateMask(mascara).multiply(FATOR_ESCALA_KG * KG_PARA_G)


def periodos_do_ano(ee, produto: str, cfg: dict, ano: int,
                    datas_ano: Sequence[dt.date], qc_max: Optional[int],
                    ) -> List[Tuple[dict, "ee.Image"]]:
    """Devolve [(rótulo, imagem em g C/m²)] para o ano: 1 item (anual) ou até
    12 itens (mensal = soma das composições 8-dias iniciadas no mês)."""
    col = ee.ImageCollection(cfg["colecao"])
    if produto == "anual":
        img = ee.Image(col.filter(ee.Filter.calendarRange(ano, ano, "year")).first())
        return [({"ano": ano},
                 _mascarar_escalar(ee, img, cfg["banda"], cfg["valido"],
                                   cfg["banda_qc"], qc_max))]

    saida = []
    for mes in range(1, 13):
        datas_mes = [d for d in datas_ano if d.month == mes]
        n = len(datas_mes)
        if n == 0:
            log(f"  AVISO: {ano}-{mes:02d} sem composições na coleção; mês ignorado.")
            continue
        esperado = 4 if mes != 12 else 3  # 46 composições/ano, ~3.8 por mês
        if n < 3:
            log(f"  AVISO: {ano}-{mes:02d} tem só {n} composição(ões) "
                f"(esperado ≈{esperado}); ano provavelmente incompleto.")
        ini = dt.date(ano, mes, 1).isoformat()
        fim = (dt.date(ano + 1, 1, 1) if mes == 12
               else dt.date(ano, mes + 1, 1)).isoformat()
        sub = col.filterDate(ini, fim).map(
            lambda im: _mascarar_escalar(ee, im, cfg["banda"], cfg["valido"],
                                         None, None))
        # Soma apenas onde todas as composições do mês são válidas.
        soma = sub.sum().updateMask(sub.count().eq(n))
        saida.append(({"ano": ano, "mes": mes, "n_composicoes": n}, soma))
    return saida


# ----------------------------------------------------------------------------
# 5. Redução: média espacial por bioma
# ----------------------------------------------------------------------------

def calcular(ee, produto: str, cfg: dict, anos: Sequence[int],
             por_ano: Dict[int, List[dt.date]], geoms: Dict[str, "ee.Geometry"],
             qc_max: Optional[int], extras: bool, tile_scale: int) -> List[dict]:
    primeira = ee.Image(ee.ImageCollection(cfg["colecao"]).first()).select(cfg["banda"])
    proj = primeira.projection()
    try:
        escala_m = proj.nominalScale().getInfo()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(f"Falha ao obter a projeção da coleção: {exc}") from exc
    log(f"Reduzindo na projeção nativa do MODIS (sinusoidal), pixel ≈ {escala_m:.1f} m.")

    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    if extras:
        reducer = (reducer
                   .combine(ee.Reducer.stdDev(), sharedInputs=True)
                   .combine(ee.Reducer.minMax(), sharedInputs=True))

    fc = ee.FeatureCollection([
        ee.Feature(g, {"bioma": nome}) for nome, g in geoms.items()])
    coluna = cfg["coluna"]
    linhas: List[dict] = []

    for ano in anos:
        log(f"Processando {ano} ...")
        periodos = periodos_do_ano(ee, produto, cfg, ano, por_ano[ano], qc_max)
        if not periodos:
            linhas.append({"ano": ano, "erro": "sem períodos com dado"})
            continue
        # Uma única requisição por ano: reduz todos os períodos e junta.
        fcs = []
        for rotulo, img in periodos:
            red = img.reduceRegions(collection=fc, reducer=reducer, crs=proj,
                                    scale=escala_m, tileScale=tile_scale)
            fcs.append(red.map(lambda f, r=rotulo: f.set(r)))
        try:
            feats = ee.FeatureCollection(fcs).flatten().getInfo().get("features", [])
        except Exception as exc:  # noqa: BLE001
            texto = str(exc)
            if "memory" in texto.lower() or "too many" in texto.lower():
                texto += ("\nDica: aumente --tile-scale (ex.: 8 ou 16) para "
                          "reduzir o uso de memória por tile.")
            log(f"  ERRO no ano {ano}: {texto}")
            linhas.append({"ano": ano, "erro": texto})
            continue

        for f in feats:
            p = f.get("properties", {})
            media, n = p.get("mean"), p.get("count")
            rotulo = {"ano": p.get("ano")}
            if produto == "mensal":
                rotulo["mes"] = p.get("mes")
            if media is None or not n:
                log(f"  AVISO: {rotulo} / {p.get('bioma')}: nenhum pixel válido.")
                linhas.append({**rotulo, "bioma": p.get("bioma"),
                               "erro": "sem pixels válidos"})
                continue
            linha = {**rotulo, "bioma": p["bioma"], coluna: media}
            if extras:
                linha.update({
                    "n_pixels": int(n),
                    "desvio_g_c_m2": p.get("stdDev"),
                    "min_g_c_m2": p.get("min"),
                    "max_g_c_m2": p.get("max"),
                })
                if produto == "mensal":
                    linha["n_composicoes"] = p.get("n_composicoes")
            linhas.append(linha)
            quando = f"{rotulo['ano']}" + (f"-{rotulo['mes']:02d}" if "mes" in rotulo else "")
            log(f"  {quando}  {p['bioma']:<15s} média = {media:8.2f} g C/m²  (n = {int(n):,})")
    return linhas


# ----------------------------------------------------------------------------
# 6. CSV
# ----------------------------------------------------------------------------

def _fmt(v, decimal: str) -> str:
    if isinstance(v, float):
        return f"{v:.4f}".replace(".", decimal)
    return "" if v is None else str(v)


def gravar_csv(linhas: List[dict], caminho: Path, produto: str, coluna: str,
               nomes_biomas: Sequence[str], extras: bool, largo: bool,
               decimal: str) -> Tuple[int, int]:
    chave = ["ano", "mes"] if produto == "mensal" else ["ano"]
    ok = [l for l in linhas if "erro" not in l]
    ok.sort(key=lambda l: tuple(l[k] for k in chave) + (l["bioma"],))
    caminho.parent.mkdir(parents=True, exist_ok=True)
    sep = ";" if decimal == "," else ","

    with caminho.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=sep)
        if largo:
            # Uma coluna por bioma (layout da planilha histórica).
            w.writerow(chave + list(nomes_biomas))
            grupos: Dict[tuple, dict] = {}
            for l in ok:
                grupos.setdefault(tuple(l[k] for k in chave), {})[l["bioma"]] = l[coluna]
            for k in sorted(grupos):
                w.writerow(list(k) + [_fmt(grupos[k].get(b), decimal)
                                      for b in nomes_biomas])
        else:
            colunas = chave + ["bioma", coluna]
            if extras:
                colunas += ["n_pixels", "desvio_g_c_m2", "min_g_c_m2", "max_g_c_m2"]
                if produto == "mensal":
                    colunas.append("n_composicoes")
            w.writerow(colunas)
            for l in ok:
                w.writerow([_fmt(l.get(c), decimal) for c in colunas])
    return len(ok), len(linhas) - len(ok)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=textwrap.dedent(__doc__).split("Uso típico")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_argument_group("Earth Engine")
    g.add_argument("--project", default=os.environ.get("EE_PROJECT"),
                   help="ID do projeto Google Cloud registrado no Earth Engine "
                        "(ou variável de ambiente EE_PROJECT).")
    g.add_argument("--autenticar", action="store_true",
                   help="Força o fluxo de autenticação (ee.Authenticate) mesmo "
                        "havendo credenciais salvas.")
    g.add_argument("--auth-mode", choices=["notebook", "localhost", "gcloud", "colab"],
                   default=None,
                   help="Modo do ee.Authenticate (padrão: automático; 'notebook' "
                        "funciona em qualquer terminal, sem gcloud).")
    g.add_argument("--service-account", help="E-mail de conta de serviço (opcional).")
    g.add_argument("--chave-json", help="Chave JSON da conta de serviço (opcional).")

    g = p.add_argument_group("Produto e período")
    g.add_argument("--produto", choices=sorted(PRODUTOS), default="anual",
                   help="'anual' = NPP do MOD17A3HGF (padrão); 'mensal' = PsnNet "
                        "do MOD17A2HGF somado por mês (formato da série 2001-2020).")
    g.add_argument("--colecao", default=None,
                   help="Sobrescreve o id da coleção (ex.: MODIS/061/MOD17A2H para "
                        "o ano corrente, ainda sem versão gap-filled).")
    g.add_argument("--banda", default=None,
                   help="Sobrescreve a banda (ex.: Gpp). Padrão: Npp ou PsnNet.")
    g.add_argument("--apenas-verificar", action="store_true",
                   help="Só autentica e informa a disponibilidade; não calcula nada.")
    g.add_argument("--inicio", type=int, default=2021,
                   help="Primeiro ano a calcular (padrão: 2021).")
    g.add_argument("--fim", type=int, default=None,
                   help="Último ano (padrão: último disponível na coleção).")

    g = p.add_argument_group("Limites dos biomas")
    g.add_argument("--biomas",
                   help="Shapefile/GeoPackage dos biomas (IBGE lm_bioma_250.shp) "
                        "OU id de asset do GEE (projects/... ou users/...).")
    g.add_argument("--bahia",
                   help="Shapefile do limite da Bahia (IBGE BA_UF_2022.shp). "
                        "Se omitido, usa FAO/GAUL 2015 do catálogo do GEE.")
    g.add_argument("--baixar-ibge", metavar="PASTA",
                   help="Baixa os shapefiles oficiais do IBGE para PASTA e os usa "
                        "como --biomas e --bahia.")
    g.add_argument("--campo-bioma", default="Bioma",
                   help="Campo com o nome do bioma (padrão: 'Bioma', como no IBGE).")
    g.add_argument("--biomas-nomes", nargs="+", default=list(BIOMAS_PADRAO),
                   help="Nomes dos biomas a processar (padrão: Mata Atlântica, "
                        "Cerrado, Caatinga).")
    g.add_argument("--tolerancia", type=float, default=0.0005,
                   help="Tolerância (graus) para simplificar os polígonos antes de "
                        "enviar ao GEE; 0 desativa (padrão 0.0005 ≈ 55 m).")

    g = p.add_argument_group("Cálculo e saída")
    g.add_argument("--qc-max", type=int, default=None,
                   help="(só --produto anual) descarta pixels com Npp_QC (%% de "
                        "entradas preenchidas) acima deste valor. Padrão: não "
                        "filtra, como na metodologia original.")
    g.add_argument("--stats-extras", action="store_true",
                   help="Inclui n_pixels, desvio-padrão, mínimo e máximo no CSV.")
    g.add_argument("--formato", choices=["longo", "largo"], default="longo",
                   help="'longo' = ano[,mes],bioma,valor (padrão); 'largo' = uma "
                        "coluna por bioma, como na planilha histórica.")
    g.add_argument("--tile-scale", type=int, default=4,
                   help="tileScale do reduceRegions (padrão 4; aumente se faltar memória).")
    g.add_argument("--saida", help="Caminho do CSV de saída "
                                   "(padrão: <produto>_biomas_bahia_<inicio>_<fim>.csv).")
    g.add_argument("--decimal", choices=[".", ","], default=".",
                   help="Separador decimal do CSV. ',' também usa ';' como "
                        "separador de campos (Excel pt-BR). Padrão '.'.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = montar_parser().parse_args(argv)
    cfg = dict(PRODUTOS[args.produto])
    if args.colecao:
        cfg["colecao"] = args.colecao
    if args.banda:
        cfg["banda"] = args.banda
        cfg["coluna"] = f"{args.banda.lower()}_g_c_m2"
    if args.qc_max is not None and not cfg["banda_qc"]:
        log("AVISO: --qc-max só se aplica ao produto anual (Npp_QC); ignorado.")

    try:
        ee = inicializar_ee(args.project, args.autenticar,
                            args.service_account, args.chave_json, args.auth_mode)

        datas = datas_disponiveis(ee, cfg["colecao"])
        por_ano = relatar_disponibilidade(datas, args.produto, cfg["colecao"])
        if args.apenas_verificar:
            print(max(por_ano))
            return 0

        anos = resolver_intervalo(por_ano, args.inicio, args.fim)
        log(f"Anos a processar: {anos}")

        caminho_biomas, caminho_bahia = args.biomas, args.bahia
        if args.baixar_ibge:
            b, ba = baixar_ibge(Path(args.baixar_ibge))
            caminho_biomas = caminho_biomas or str(b)
            caminho_bahia = caminho_bahia or str(ba)
        if not caminho_biomas:
            raise ErroPipeline(
                "Nenhum limite de biomas informado.\n"
                "Opções:\n"
                "  --baixar-ibge PASTA      baixa os limites oficiais do IBGE\n"
                "  --biomas ARQ.shp         shapefile local (IBGE ou o da dissertação)\n"
                "  --biomas projects/.../x  asset (FeatureCollection) já no GEE"
            )

        log("\nPreparando limites dos biomas na Bahia:")
        if caminho_biomas.startswith(("projects/", "users/")):
            geoms = biomas_asset(ee, caminho_biomas, caminho_bahia,
                                 args.campo_bioma, args.biomas_nomes, args.tolerancia)
        else:
            geoms = biomas_locais(ee, caminho_biomas, caminho_bahia,
                                  args.campo_bioma, args.biomas_nomes, args.tolerancia)

        log("")
        linhas = calcular(ee, args.produto, cfg, anos, por_ano, geoms,
                          args.qc_max, args.stats_extras, args.tile_scale)

        saida = Path(args.saida) if args.saida else Path(
            f"{args.produto}_biomas_bahia_{anos[0]}_{anos[-1]}.csv")
        n_ok, n_err = gravar_csv(linhas, saida, args.produto, cfg["coluna"],
                                 args.biomas_nomes, args.stats_extras,
                                 args.formato == "largo", args.decimal)
        log(f"\nCSV gravado: {saida}  ({n_ok} registros)")
        if n_err:
            log(f"AVISO: {n_err} registro(s) falharam e ficaram fora do CSV "
                "(veja mensagens acima).")
            return 2
        return 0
    except ErroPipeline as exc:
        falhar(str(exc))
    except KeyboardInterrupt:
        falhar("interrompido pelo usuário.", 130)
    return 1


if __name__ == "__main__":
    sys.exit(main())
