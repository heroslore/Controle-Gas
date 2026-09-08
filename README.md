# Controle do Gás

Controle simples para depósito de gás: vendas, fiado, estoque e histórico.
Funciona no celular, direto no navegador, sem instalar nada.

## Endereço

Depois que este projeto estiver no branch `main`, o sistema fica publicado em:

**https://heroslore.github.io/Controle-Gas/**

No celular, abra o endereço no Chrome e use "Adicionar à tela inicial" para virar um ícone como um aplicativo.

## Como usar

- **Vender**: escolha o produto, a quantidade, o pagamento (Dinheiro, Pix, Cartão ou Fiado) e toque em *Registrar venda*. Fiado exige o nome do cliente.
- **Fiado**: mostra quem está devendo. Toque em *Recebi* quando o cliente pagar.
- **Estoque**: cada venda desconta do estoque. Quando chegar carga, digite quantos entraram e toque em *Entrou*.
- **Histórico**: total do dia, do mês ou de tudo, separado por forma de pagamento. Dá para apagar uma venda errada.
- **Mais**: nome do depósito, produtos e preços, backup, informações de suporte.

## Onde ficam os dados

Os dados ficam salvos **no próprio aparelho** (no navegador). Por isso:

- Não limpe os dados do navegador, senão o histórico some.
- De vez em quando faça **Mais → Gerar backup → Copiar backup** e mande o texto por WhatsApp para alguém guardar.
- Para colocar em outro aparelho: **Mais → Restaurar backup** e cole o texto.

## Se der erro

1. Aparece uma faixa vermelha no topo com o erro. Toque em **Copiar erro**.
2. Ou vá em **Mais → Ajuda e suporte → Copiar informações**.
3. Mande o texto copiado por WhatsApp para quem cuida do sistema.

O texto traz a versão, o aparelho, quantas vendas existem e o último erro registrado, o que permite ajudar à distância.

## Publicação

O arquivo `index.html` é o sistema inteiro. O workflow em `.github/workflows/pages.yml` publica automaticamente no GitHub Pages a cada alteração no branch `main`.
