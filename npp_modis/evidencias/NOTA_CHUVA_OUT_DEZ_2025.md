# Por que a precipitação de out–dez/2025 ainda não existe (verificado em 17/09/2026)

## 1. O produto oficial termina em setembro de 2025

Servidor da NASA (GES DISC), pasta do IMERG Final mensal V07:
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/2025/

Últimos arquivos publicados (nome do arquivo → data de publicação):

| Mês | Arquivo | Publicado em |
|---|---|---|
| jun/2025 | 3B-MO.MS.MRG.3IMERG.20250601-…V07B.HDF5 | 03/11/2025 |
| jul/2025 | 3B-MO.MS.MRG.3IMERG.20250701-…V07B.HDF5 | 01/12/2025 |
| ago/2025 | 3B-MO.MS.MRG.3IMERG.20250801-…V07B.HDF5 | 22/12/2025 |
| **set/2025** | 3B-MO.MS.MRG.3IMERG.20250901-…V07B.HDF5 | **02/02/2026** |

Não há arquivo de outubro, novembro ou dezembro de 2025, e a pasta de 2026
(https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/2026/) não
existe (HTTP 404). Capturas: `nasa_imerg_2025.png`, `nasa_imerg_2026.png`.

O Google Earth Engine espelha exatamente isso: a coleção
`NASA/GPM_L3/IMERG_MONTHLY_V07` termina em 2025-09-01
(https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_MONTHLY_V07).

## 2. Aviso oficial da NASA: a versão V07 foi encerrada em set/2025

**"IMERG V08 Transition Schedule"**, 28/04/2026
https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule

> "For the Final Run, the V07 record ends in September 2025 because the parent
> products feeding into the IMERG algorithm (CORRA and GPROF) are being
> upgraded to V08. […] The IMERG V08 Final Run is planned for release in the
> summer of 2026 [and will provide] a retrospective processing of the full
> record, starting from January 1998 to the present day."

**"Update to the IMERG V08 Transition Schedule, Aug. 2026"**, 06/08/2026
https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026

> "At this moment, the IMERG development team is still waiting for V08 of one
> of the parent products to IMERG to be finalized. […] it seems more likely
> that IMERG V08 Final Run will be released in the fall of 2026."

Capturas: `nasa_aviso_v08_abr2026.png`, `nasa_aviso_v08_ago2026.png`.

## 3. O que isso significa para a dissertação

- Os meses out–dez/2025 **nunca sairão na V07**. Só existirão na V08, prevista
  para o outono de 2026 no hemisfério norte (set–nov/2026), e a V08 vai
  reprocessar toda a série desde 1998.
- Existe a versão "Late Run" V07 (meias-horas, quase em tempo real) para esses
  meses, mas ela não é calibrada por pluviômetros; testada aqui, ficou 35–85 %
  abaixo do Final nos meses secos de 2025. Por isso não foi usada.
- Opções: (a) manter a série até set/2025 (n = 297) e registrar o motivo; (b)
  quando a V08 sair, reprocessar toda a chuva 2001–2025 na V08 (um comando no
  script) e completar os 300 meses.
