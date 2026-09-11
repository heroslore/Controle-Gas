#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Variáveis MODIS/GPM por bioma na Bahia via Google Earth Engine, no formato da
série histórica de Benfica et al. (2022, 2023).

Variáveis (--variavel, pode repetir; 'todas' = todas as mensais):

  npp       MODIS/061/MOD17A3HGF  Npp          NPP anual (g C/m²/ano)
  psn       MODIS/061/MOD17A2HGF  PsnNet       fotossíntese líquida mensal (g C/m²)
  et        MODIS/061/MOD16A2GF   ET           evapotranspiração mensal (mm)
  pet       MODIS/061/MOD16A2GF   PET          ET potencial mensal (mm)
  ida       = et / pet                         índice de disponibilidade de água (WAI)
  lst       MODIS/061/MOD11A2     LST_Day_1km  temperatura de superfície diurna (°C)
  precip    NASA/GPM_L3/IMERG_MONTHLY_V07      precipitação mensal (mm)
  queimada  MODIS/061/MCD64A1     BurnDate     área queimada mensal (ha = pixels x 25)
  oni       NOAA CPC (download)                Oceanic Niño Index (mês central)

Produtos 8-dias (psn, et, pet, lst) são agregados por mês com --agregacao:
'benfica' (janelas fixas de DOY da planilha histórica, padrão) ou 'calendario'.

Uso típico:

    python npp_modis_gee.py --project MEU-PROJETO --variavel todas \
        --baixar-ibge dados_ibge --inicio 2021 --formato largo

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

# tipo: 'anual' (1 imagem/ano), '8dias' (46 composições/ano, agregadas por mês),
#       'mensal' (1 imagem/mês).  agreg: como juntar as composições do mês.
#       reducer: 'mean' (média espacial) ou 'count' (n. de pixels).
VARIAVEIS = {
    "npp": dict(colecao="MODIS/061/MOD17A3HGF", banda="Npp", escala=0.1,
                valido=(-30000, 32700), banda_qc="Npp_QC", tipo="anual",
                agreg="valor", reducer="mean", coluna="npp_g_c_m2"),
    "psn": dict(colecao="MODIS/061/MOD17A2HGF", banda="PsnNet", escala=0.1,
                valido=(-30000, 30000), tipo="8dias", agreg="soma",
                reducer="mean", coluna="psn_g_c_m2"),
    "et": dict(colecao="MODIS/061/MOD16A2GF", banda="ET", escala=0.1,
               valido=(-32767, 32700), tipo="8dias", agreg="soma",
               reducer="mean", coluna="et_mm"),
    "pet": dict(colecao="MODIS/061/MOD16A2GF", banda="PET", escala=0.1,
                valido=(-32767, 32700), tipo="8dias", agreg="soma",
                reducer="mean", coluna="pet_mm"),
    "lst": dict(colecao="MODIS/061/MOD11A2", banda="LST_Day_1km", escala=0.02,
                offset=-273.15, valido=(7500, 65535), tipo="8dias",
                agreg="media", reducer="mean", coluna="lst_dia_c"),
    "precip": dict(colecao="NASA/GPM_L3/IMERG_MONTHLY_V07", banda="precipitation",
                   escala=1.0, valido=(0, 1e9), tipo="mensal", agreg="mmh_x_horas",
                   reducer="mean", coluna="precip_mm",
                   # meses ainda sem o produto mensal (Final, ~6 meses de atraso):
                   # média das meias-horas do IMERG V07 (inclui Late run) x horas.
                   reserva="NASA/GPM_L3/IMERG_V07"),
    "queimada": dict(colecao="MODIS/061/MCD64A1", banda="BurnDate", escala=1.0,
                     valido=(1, 366), tipo="mensal", agreg="contagem",
                     reducer="count", coluna="area_queimada_ha", ha_por_pixel=25.0),
}
DERIVADAS = {"ida": ("et", "pet")}          # ida = et / pet (razão das médias mensais)
MENSAIS = ["psn", "et", "pet", "ida", "lst", "precip", "queimada"]
ALIAS_PRODUTO = {"anual": ["npp"], "mensal": ["psn"]}

LOTE = 12   # reduções por requisição ao GEE
# Meses sem o IMERG mensal Final: estimar pela média das meias-horas (Late run)?
# Desligado por padrão: em 2025 o Late run ficou 35-85 % abaixo do Final nos
# meses secos da Bahia. Ligue com --precip-provisoria só para uma prévia.
PRECIP_PROVISORIA = False
URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ESTACOES_ONI = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS",
                "ASO", "SON", "OND", "NDJ"]

# MOD17: DN x 0,0001 kg C/m² x 1000 = DN x 0,1 g C/m² (o mesmo 0,1 do MRT/ArcGIS).
# MOD16: DN x 0,1 kg/m²/8 dias = mm. MOD11: DN x 0,02 K - 273,15 = °C.

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


def relatar_disponibilidade(datas: Sequence[dt.date], tipo: str,
                            colecao: str) -> Dict[int, List[dt.date]]:
    por_ano: Dict[int, List[dt.date]] = {}
    for d in datas:
        por_ano.setdefault(d.year, []).append(d)
    anos = sorted(por_ano)
    log(f"\n{colecao}: {len(datas)} imagens, {anos[0]} a {anos[-1]}.")
    ultimo = anos[-1]
    n = len(por_ano[ultimo])
    if tipo == "anual":
        log(f"ÚLTIMO ANO DISPONÍVEL: {ultimo}")
    elif tipo == "8dias":
        log(f"Última composição 8-dias: {datas[-1].isoformat()}  ({n} de 46 em {ultimo})")
        completo = ultimo if n >= 46 else (ultimo - 1 if ultimo - 1 in por_ano else None)
        log(f"ÚLTIMO ANO COMPLETO (46 composições): {completo}")
    else:
        log(f"Última imagem mensal: {datas[-1].isoformat()}  ({n} de 12 meses em {ultimo})")
        completo = ultimo if n >= 12 else (ultimo - 1 if ultimo - 1 in por_ano else None)
        log(f"ÚLTIMO ANO COMPLETO (12 meses): {completo}")
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

def _mascarar_escalar(ee, img, cfg: dict, qc_max: Optional[int]):
    b = img.select(cfg["banda"])
    vmin, vmax = cfg["valido"]
    mascara = b.gte(vmin).And(b.lte(vmax))
    if cfg.get("banda_qc") and qc_max is not None:
        mascara = mascara.And(img.select(cfg["banda_qc"]).lte(qc_max))
    out = b.updateMask(mascara).multiply(cfg["escala"])
    if cfg.get("offset"):
        out = out.add(cfg["offset"])
    return out


# Regra de agregação da série histórica (Benfica et al. 2022 / planilha
# "dados_graficos_Benfica"), descoberta por comparação com os dados 2001-2020:
# cada mês = soma de 4 composições 8-dias consecutivas em janelas FIXAS de DOY
# (sem ajuste de ano bissexto). Janeiro usa a última composição do ano anterior
# (DOY 361) + DOY 1, 9 e 17; a composição DOY 337 entra em novembro E em
# dezembro. Reproduz a planilha com erro mediano < 0,3 % em todos os meses.
JANELAS_BENFICA: Dict[int, List[int]] = {
    1: [-361, 1, 9, 17],          # negativo = DOY do ano anterior
    **{m: [8 * k + 1 for k in range(4 * (m - 1) - 1, 4 * (m - 1) + 3)]
       for m in range(2, 12)},    # fev 25-49, mar 57-81, ..., nov 313-337
    12: [337, 345, 353, 361],
}


def _data_doy(ano: int, doy: int) -> dt.date:
    if doy < 0:
        return dt.date(ano - 1, 1, 1) + dt.timedelta(days=-doy - 1)
    return dt.date(ano, 1, 1) + dt.timedelta(days=doy - 1)


def periodos_do_ano(ee, cfg: dict, ano: int, por_ano: Dict[int, List[dt.date]],
                    qc_max: Optional[int], agregacao: str = "benfica",
                    ) -> List[Tuple[dict, "ee.Image"]]:
    """Devolve [(rótulo, imagem já escalada)] para o ano: 1 item (anual) ou até
    12 itens (8dias/mensal). Agregação dos produtos 8-dias:
      'benfica'    = janelas fixas de DOY da série histórica (JANELAS_BENFICA);
      'calendario' = composições iniciadas dentro do mês civil."""
    col = ee.ImageCollection(cfg["colecao"])
    tipo = cfg["tipo"]
    if tipo == "anual":
        img = ee.Image(col.filter(ee.Filter.calendarRange(ano, ano, "year")).first())
        return [({"ano": ano}, _mascarar_escalar(ee, img, cfg, qc_max))]

    datas_ano = por_ano.get(ano, [])
    existentes = set(datas_ano) | set(por_ano.get(ano - 1, []))
    saida = []
    for mes in range(1, 13):
        ini = dt.date(ano, mes, 1)
        fim = dt.date(ano + 1, 1, 1) if mes == 12 else dt.date(ano, mes + 1, 1)
        if tipo == "mensal":
            datas_mes = [d for d in datas_ano if d.month == mes]
            provisorio = 0
            if datas_mes:
                img = ee.Image(col.filterDate(ini.isoformat(), fim.isoformat()).first())
                img = _mascarar_escalar(ee, img, cfg, None)
            elif cfg.get("reserva") and PRECIP_PROVISORIA and dt.date.today() > fim:
                # Produto mensal ainda não publicado: usa a coleção de reserva
                # (meias-horas), média do mês. Marcado como provisório.
                log(f"  AVISO: {ano}-{mes:02d} ainda sem {cfg['colecao']}; usando "
                    f"média de {cfg['reserva']} (provisório).")
                sub = (ee.ImageCollection(cfg["reserva"])
                       .filterDate(ini.isoformat(), fim.isoformat()).select(cfg["banda"]))
                img = sub.mean().multiply(cfg["escala"])
                provisorio = 1
            else:
                log(f"  AVISO: {ano}-{mes:02d} sem imagem em {cfg['colecao']}; mês ignorado.")
                continue
            if cfg["agreg"] == "mmh_x_horas":          # IMERG: mm/h -> mm/mês
                img = img.multiply(24 * (fim - ini).days)
            saida.append(({"ano": ano, "mes": mes, "n_composicoes": 1,
                           "provisorio": provisorio}, img))
            continue

        if agregacao == "benfica":
            datas_mes = [_data_doy(ano, d) for d in JANELAS_BENFICA[mes]]
            faltam = [d for d in datas_mes if d not in existentes]
            if faltam and cfg["agreg"] == "media" and len(datas_mes) - len(faltam) >= 2:
                # Média tolera composição ausente (ex.: MOD11A2 2001-06-18).
                log(f"  AVISO: {ano}-{mes:02d} sem composição(ões) "
                    f"{[d.isoformat() for d in faltam]} em {cfg['colecao']}; "
                    "média das disponíveis.")
                datas_mes = [d for d in datas_mes if d not in faltam]
            elif faltam:
                log(f"  AVISO: {ano}-{mes:02d} sem composição(ões) "
                    f"{[d.isoformat() for d in faltam]} em {cfg['colecao']}; mês ignorado.")
                continue
            filtro = ee.Filter.Or(*[
                ee.Filter.date(d.isoformat(), (d + dt.timedelta(days=1)).isoformat())
                for d in datas_mes])
            sub = col.filter(filtro)
        else:
            datas_mes = [d for d in datas_ano if d.month == mes]
            if not datas_mes:
                log(f"  AVISO: {ano}-{mes:02d} sem composições; mês ignorado.")
                continue
            if len(datas_mes) < 3:
                log(f"  AVISO: {ano}-{mes:02d} tem só {len(datas_mes)} "
                    "composição(ões) (esperado 3-4); ano provavelmente incompleto.")
            sub = col.filterDate(ini.isoformat(), fim.isoformat())
        n = len(datas_mes)
        sub = sub.map(lambda im: _mascarar_escalar(ee, im, cfg, None))
        if cfg["agreg"] == "media":
            # Média das médias espaciais de cada composição (como na planilha):
            # cada composição é reduzida separadamente e combinada em calcular().
            lista = sub.toList(n)
            for i in range(n):
                saida.append(({"ano": ano, "mes": mes, "n_composicoes": n,
                               "comp": i}, ee.Image(lista.get(i))))
            continue
        # Soma: pixel só entra se todas as composições do mês forem válidas.
        agg = sub.sum().updateMask(sub.count().eq(n))
        saida.append(({"ano": ano, "mes": mes, "n_composicoes": n}, agg))
    return saida


# ----------------------------------------------------------------------------
# 5. Redução: média espacial por bioma
# ----------------------------------------------------------------------------

def calcular(ee, nome: str, cfg: dict, anos: Sequence[int],
             por_ano: Dict[int, List[dt.date]], geoms: Dict[str, "ee.Geometry"],
             qc_max: Optional[int], extras: bool, tile_scale: int,
             agregacao: str = "benfica") -> List[dict]:
    primeira = ee.Image(ee.ImageCollection(cfg["colecao"]).first()).select(cfg["banda"])
    proj = primeira.projection()
    try:
        escala_m = proj.nominalScale().getInfo()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(f"Falha ao obter a projeção de {cfg['colecao']}: {exc}") from exc
    log(f"[{nome}] {cfg['colecao']} banda {cfg['banda']}, pixel ≈ {escala_m:.0f} m, "
        f"reduzindo na projeção nativa.")

    if cfg["reducer"] == "count":
        reducer = ee.Reducer.count()
    else:
        reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
        if extras:
            reducer = (reducer
                       .combine(ee.Reducer.stdDev(), sharedInputs=True)
                       .combine(ee.Reducer.minMax(), sharedInputs=True))

    fc = ee.FeatureCollection([
        ee.Feature(g, {"bioma": b}) for b, g in geoms.items()])
    coluna = cfg["coluna"]
    linhas: List[dict] = []

    for ano in anos:
        log(f"[{nome}] {ano} ...")
        periodos = periodos_do_ano(ee, cfg, ano, por_ano, qc_max, agregacao)
        if not periodos:
            linhas.append({"ano": ano, "variavel": nome, "erro": "sem períodos com dado"})
            continue
        # Lotes de até LOTE reduções por requisição (limite de agregações
        # simultâneas do GEE).
        feats: List[dict] = []
        falhou = False
        for i in range(0, len(periodos), LOTE):
            fcs = []
            for rotulo, img in periodos[i:i + LOTE]:
                red = img.reduceRegions(collection=fc, reducer=reducer, crs=proj,
                                        scale=escala_m, tileScale=tile_scale)
                fcs.append(red.map(lambda f, r=rotulo: f.set(r)))
            try:
                feats += ee.FeatureCollection(fcs).flatten().getInfo().get("features", [])
            except Exception as exc:  # noqa: BLE001
                texto = str(exc)
                if "memory" in texto.lower() or "too many" in texto.lower():
                    texto += ("\nDica: aumente --tile-scale (ex.: 8 ou 16), ou rode "
                              "uma variável por vez.")
                log(f"  ERRO em {nome} {ano}: {texto}")
                linhas.append({"ano": ano, "variavel": nome, "erro": texto})
                falhou = True
                break
        if falhou:
            continue

        if cfg["agreg"] == "media":
            feats = _combinar_composicoes(feats)
        for f in feats:
            p = f.get("properties", {})
            rotulo = {"ano": p.get("ano")}
            if cfg["tipo"] != "anual":
                rotulo["mes"] = p.get("mes")
            if cfg["reducer"] == "count":
                valor = float(p.get("count") or 0) * cfg.get("ha_por_pixel", 1.0)
                n = p.get("count") or 0
            else:
                valor, n = p.get("mean"), p.get("count")
                if valor is None or not n:
                    log(f"  AVISO: {nome} {rotulo} / {p.get('bioma')}: nenhum pixel válido.")
                    linhas.append({**rotulo, "bioma": p.get("bioma"), "variavel": nome,
                                   "erro": "sem pixels válidos"})
                    continue
            linha = {**rotulo, "bioma": p["bioma"], "variavel": nome, coluna: valor}
            if p.get("provisorio"):
                linha["provisorio"] = nome
            if extras and cfg["reducer"] != "count":
                linha.update({"n_pixels": int(n), "desvio": p.get("stdDev"),
                              "min": p.get("min"), "max": p.get("max"),
                              "n_composicoes": p.get("n_composicoes")})
            linhas.append(linha)
            quando = f"{rotulo['ano']}" + (f"-{rotulo['mes']:02d}" if "mes" in rotulo else "")
            log(f"  {quando}  {p['bioma']:<15s} {coluna} = {valor:10.3f}")
    return linhas


def _combinar_composicoes(feats: List[dict]) -> List[dict]:
    """Agrupa reduções por composição em uma por (ano, mes, bioma): média das
    médias espaciais das composições com pixels válidos; count = mínimo."""
    grupos: Dict[tuple, List[dict]] = {}
    for f in feats:
        p = f.get("properties", {})
        grupos.setdefault((p.get("ano"), p.get("mes"), p.get("bioma")), []).append(p)
    saida = []
    for (ano, mes, bioma), ps in sorted(grupos.items(), key=lambda kv: str(kv[0])):
        validos = [p for p in ps if p.get("mean") is not None and p.get("count")]
        base = dict(ps[0]); base.pop("comp", None)
        if validos:
            base["mean"] = sum(p["mean"] for p in validos) / len(validos)
            base["count"] = min(p["count"] for p in validos)
            base["n_composicoes"] = len(validos)
            if len(validos) < len(ps):
                log(f"  AVISO: {ano}-{mes:02d} {bioma}: só {len(validos)} de {len(ps)} "
                    "composições com pixels válidos; média das disponíveis.")
        else:
            base["mean"], base["count"] = None, 0
        saida.append({"properties": base})
    return saida


def baixar_oni(anos: Sequence[int]) -> Dict[Tuple[int, int], float]:
    """ONI (NOAA CPC): valor de cada estação de 3 meses atribuído ao mês central."""
    try:
        with urllib.request.urlopen(URL_ONI, timeout=60) as r:  # noqa: S310
            texto = r.read().decode()
    except Exception as exc:  # noqa: BLE001
        raise ErroPipeline(f"Falha ao baixar o ONI de {URL_ONI}: {exc}") from exc
    out = {}
    for lin in texto.splitlines()[1:]:
        partes = lin.split()
        if len(partes) < 4 or partes[0] not in ESTACOES_ONI:
            continue
        ano, mes = int(partes[1]), ESTACOES_ONI.index(partes[0]) + 1
        if ano in anos:
            out[(ano, mes)] = float(partes[3])
    if not out:
        raise ErroPipeline("ONI baixado mas sem linhas para os anos pedidos.")
    log(f"ONI: {len(out)} meses obtidos de {URL_ONI}")
    return out


# ----------------------------------------------------------------------------
# 6. CSV
# ----------------------------------------------------------------------------

def _fmt(v, decimal: str) -> str:
    if isinstance(v, float):
        return f"{v:.4f}".replace(".", decimal)
    return "" if v is None else str(v)


def montar_tabela(linhas: List[dict], nomes: Sequence[str],
                  oni: Optional[Dict[Tuple[int, int], float]]) -> Tuple[List[dict], List[str]]:
    """Junta as variáveis numa tabela tidy: ano[, mes], bioma, <col de cada var>."""
    ok = [l for l in linhas if "erro" not in l]
    mensal = any("mes" in l for l in ok)
    chave = ["ano", "mes"] if mensal else ["ano"]
    colunas = [VARIAVEIS[n]["coluna"] if n in VARIAVEIS else n
               for n in nomes if n in VARIAVEIS or n in DERIVADAS]
    tab: Dict[tuple, dict] = {}
    for l in ok:
        k = tuple(l.get(c) for c in chave) + (l["bioma"],)
        d = tab.setdefault(k, {c: l.get(c) for c in chave} | {"bioma": l["bioma"]})
        d[VARIAVEIS[l["variavel"]]["coluna"]] = l[VARIAVEIS[l["variavel"]]["coluna"]]
        if l.get("provisorio"):
            d["provisorio"] = ";".join(filter(None, [d.get("provisorio"), l["provisorio"]]))
    for nome, (a, b) in DERIVADAS.items():
        if nome in nomes:
            ca, cb, cn = VARIAVEIS[a]["coluna"], VARIAVEIS[b]["coluna"], nome
            for d in tab.values():
                if d.get(ca) is not None and d.get(cb):
                    d[cn] = d[ca] / d[cb]
    if oni is not None and mensal:
        colunas.append("oni")
        for d in tab.values():
            d["oni"] = oni.get((d["ano"], d["mes"]))
    registros = [tab[k] for k in sorted(tab)]
    if any(r.get("provisorio") for r in registros):
        colunas.append("provisorio")
    return registros, chave + ["bioma"] + colunas


def gravar_csv(registros: List[dict], colunas: List[str], caminho: Path,
               nomes_biomas: Sequence[str], largo: bool, decimal: str) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    sep = ";" if decimal == "," else ","
    chave = [c for c in colunas if c in ("ano", "mes")]
    vars_ = [c for c in colunas if c not in ("ano", "mes", "bioma")]
    with caminho.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=sep)
        if largo:
            # Layout da planilha: ano, mes, [oni], <bioma>_<variável> ...
            v_bioma = [v for v in vars_ if v != "oni"]
            cab = chave + (["oni"] if "oni" in vars_ else []) + \
                  [f"{b}_{v}" for v in v_bioma for b in nomes_biomas]
            w.writerow(cab)
            grupos: Dict[tuple, dict] = {}
            for r in registros:
                grupos.setdefault(tuple(r[c] for c in chave), {})[r["bioma"]] = r
            for k in sorted(grupos):
                g = grupos[k]; qualquer = next(iter(g.values()))
                lin = list(k) + ([_fmt(qualquer.get("oni"), decimal)] if "oni" in vars_ else [])
                lin += [_fmt(g.get(b, {}).get(v), decimal) for v in v_bioma for b in nomes_biomas]
                w.writerow(lin)
            return len(grupos)
        w.writerow(colunas)
        for r in registros:
            w.writerow([_fmt(r.get(c), decimal) for c in colunas])
    return len(registros)


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

    g = p.add_argument_group("Variáveis e período")
    g.add_argument("--variavel", nargs="+", default=None,
                   choices=sorted(VARIAVEIS) + sorted(DERIVADAS) + ["oni", "todas"],
                   help="Uma ou mais variáveis (padrão: psn). 'todas' = "
                        + ", ".join(MENSAIS) + " + oni. 'npp' (anual) sai em CSV separado.")
    g.add_argument("--produto", choices=sorted(ALIAS_PRODUTO), default=None,
                   help="Atalho antigo: 'anual' = --variavel npp; 'mensal' = --variavel psn.")
    g.add_argument("--colecao", default=None,
                   help="Sobrescreve a coleção da (única) variável pedida "
                        "(ex.: MODIS/061/MOD17A2H para o ano corrente, sem gap-fill).")
    g.add_argument("--banda", default=None,
                   help="Sobrescreve a banda da (única) variável pedida (ex.: Gpp).")
    g.add_argument("--apenas-verificar", action="store_true",
                   help="Só autentica e informa a disponibilidade; não calcula nada.")
    g.add_argument("--inicio", type=int, default=2021,
                   help="Primeiro ano a calcular (padrão: 2021).")
    g.add_argument("--fim", type=int, default=None,
                   help="Último ano (padrão: último disponível em cada coleção).")

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
    g.add_argument("--agregacao", choices=["benfica", "calendario"],
                   default="benfica",
                   help="(produtos 8-dias) 'benfica' = janelas fixas de DOY da série "
                        "histórica 2001-2020 (jan = DOY 361 do ano anterior + 1, 9, 17; "
                        "fev = 25-49; ...; dez = 337-361), padrão; 'calendario' = "
                        "composições iniciadas dentro do mês civil.")
    g.add_argument("--precip-provisoria", action="store_true",
                   help="Preenche meses ainda sem IMERG mensal Final com a média das "
                        "meias-horas (Late run), marcados como 'provisorio'. Padrão: "
                        "deixa em branco (o Late run subestima muito os meses secos).")
    g.add_argument("--stats-extras", action="store_true",
                   help="Inclui n_pixels, desvio-padrão, mínimo e máximo no CSV.")
    g.add_argument("--formato", choices=["longo", "largo"], default="longo",
                   help="'longo' = ano[,mes],bioma,<uma coluna por variável> (padrão); "
                        "'largo' = ano,mes,[oni],<bioma>_<variável>..., como a aba "
                        "Plan1 da planilha histórica.")
    g.add_argument("--tile-scale", type=int, default=4,
                   help="tileScale do reduceRegions (padrão 4; aumente se faltar memória).")
    g.add_argument("--saida", help="Caminho do CSV de saída (padrão: "
                                   "variaveis_biomas_bahia_<inicio>_<fim>.csv; o NPP "
                                   "anual vai para npp_anual_biomas_bahia_<...>.csv).")
    g.add_argument("--decimal", choices=[".", ","], default=".",
                   help="Separador decimal do CSV. ',' também usa ';' como "
                        "separador de campos (Excel pt-BR). Padrão '.'.")
    return p


def _resolver_variaveis(args) -> Tuple[List[str], bool]:
    nomes = list(args.variavel or [])
    if args.produto:
        nomes += ALIAS_PRODUTO[args.produto]
    if not nomes:
        nomes = ["psn"]
    if "todas" in nomes:
        nomes = [n for n in nomes if n != "todas"] + MENSAIS + ["oni"]
    # dependências das derivadas
    for d, deps in DERIVADAS.items():
        if d in nomes:
            for x in deps:
                if x not in nomes:
                    nomes.append(x)
    quer_oni = "oni" in nomes
    ordenado = [n for n in ["npp"] + MENSAIS if n in nomes]   # ida fica após pet
    return ordenado, quer_oni


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = montar_parser().parse_args(argv)
    global PRECIP_PROVISORIA
    PRECIP_PROVISORIA = bool(args.precip_provisoria)
    nomes, quer_oni = _resolver_variaveis(args)
    cfgs = {n: dict(VARIAVEIS[n]) for n in nomes if n in VARIAVEIS}
    if args.colecao or args.banda:
        if len(cfgs) != 1:
            falhar("--colecao/--banda só valem com uma única variável.")
        (unica,) = cfgs
        if args.colecao:
            cfgs[unica]["colecao"] = args.colecao
        if args.banda:
            cfgs[unica]["banda"] = args.banda
            cfgs[unica]["coluna"] = f"{args.banda.lower()}_{cfgs[unica]['coluna'].split('_', 1)[-1]}"
    if args.qc_max is not None and not any(c.get("banda_qc") for c in cfgs.values()):
        log("AVISO: --qc-max só se aplica ao NPP anual (Npp_QC); ignorado.")

    try:
        ee = inicializar_ee(args.project, args.autenticar,
                            args.service_account, args.chave_json, args.auth_mode)

        disponibilidade = {}
        for n, cfg in cfgs.items():
            datas = datas_disponiveis(ee, cfg["colecao"])
            disponibilidade[n] = relatar_disponibilidade(datas, cfg["tipo"], cfg["colecao"])
        if args.apenas_verificar:
            for n, por_ano in disponibilidade.items():
                print(f"{n}\t{max(por_ano)}")
            return 0

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

        linhas: List[dict] = []
        anos_todos: set = set()
        for n, cfg in cfgs.items():
            log("")
            anos = resolver_intervalo(disponibilidade[n], args.inicio, args.fim)
            anos_todos.update(anos)
            log(f"[{n}] anos a processar: {anos}")
            linhas += calcular(ee, n, cfg, anos, disponibilidade[n], geoms,
                               args.qc_max, args.stats_extras, args.tile_scale,
                               args.agregacao)

        oni = baixar_oni(sorted(anos_todos)) if quer_oni else None
        n_err = sum("erro" in l for l in linhas)
        anos_ord = sorted(anos_todos)
        sufixo = f"_{anos_ord[0]}_{anos_ord[-1]}"
        base = Path(args.saida) if args.saida else Path(f"variaveis_biomas_bahia{sufixo}.csv")

        mensais = [l for l in linhas if l.get("variavel") != "npp"]
        anuais = [l for l in linhas if l.get("variavel") == "npp"]
        if mensais:
            reg, cols = montar_tabela(mensais, [n for n in nomes if n != "npp"], oni)
            k = gravar_csv(reg, cols, base, args.biomas_nomes,
                           args.formato == "largo", args.decimal)
            log(f"\nCSV gravado: {base}  ({k} linhas; colunas: {', '.join(cols)})")
        if anuais:
            reg, cols = montar_tabela(anuais, ["npp"], None)
            destino = base.with_name(f"npp_anual_biomas_bahia{sufixo}.csv") if mensais \
                else base
            k = gravar_csv(reg, cols, destino, args.biomas_nomes,
                           args.formato == "largo", args.decimal)
            log(f"CSV gravado: {destino}  ({k} linhas)")
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
