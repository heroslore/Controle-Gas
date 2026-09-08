# Controle Semanal — Gás e Água

Controle simples para depósito de gás e água: semana de trabalho, vendas, saídas do caminhão, gastos, fiado, rotas e resumo.
Funciona no celular, direto no navegador, sem instalar nada.

## Endereço

Depois que este projeto estiver no branch `main`, o sistema fica publicado em:

**https://heroslore.github.io/Controle-Gas/**

No celular, abra o endereço no Chrome e use "Adicionar à tela inicial" para virar um ícone como um aplicativo.

## Onde ficam os dados

Os dados ficam salvos **no próprio aparelho** (no navegador, via localStorage). Por isso:

- Não limpe os dados do navegador, senão o histórico some.
- Use sempre o mesmo navegador no mesmo aparelho.
- O botão "Zerar TUDO" apaga todas as semanas e não tem volta.

## Publicação

O arquivo `index.html` é o sistema inteiro. O workflow em `.github/workflows/pages.yml` publica automaticamente no GitHub Pages a cada alteração no branch `main`.
Para atualizar o sistema, basta substituir o `index.html` e enviar para o `main`.
