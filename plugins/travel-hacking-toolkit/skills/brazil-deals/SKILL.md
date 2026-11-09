---
name: brazil-deals
description: Como monitorar e ler fontes brasileiras de promocao de passagens e milhas. Passageiro de Primeira, Melhores Destinos, Pontos pra Voar, Viaja na Milha, Farejador de Milhas. Never treat blog prices as live facts. Load when hunting Brazilian transfer bonuses, milheiro tables, or fare alerts.
category: reference
summary: Fontes BR de promo (PdP, Melhores Destinos, Viaja na Milha, Farejador). Como ler, nunca copiar preco.
---

# Fontes brasileiras de promo

**Dados:** `data/brazil-deal-sources.json`

Estas fontes sao para **monitorar** e para **extrair inputs**. O preco impresso num post e um snapshot. Recalcule o milheiro com o skill `milheiro` e mande o usuario confirmar no site do programa.

## Fontes

| Fonte | URL | O que e | Como ler |
|-------|-----|---------|----------|
| Passageiro de Primeira | https://www.passageirodeprimeira.com | Analise de milheiro, clube, transferencia | Use a tabela do post como roteiro da conta. Extraia preco/bonus/clube. Recalcule. |
| Melhores Destinos | https://www.melhoresdestinos.com.br | Alerta de tarifa cash e calendarios de promo | Confirme origem (muitos alertas sao GRU, nao NAT). REC/FOR importam para TAP. Error fare some. |
| Pontos pra Voar | https://www.pontospravoar.com.br | Educacao + campanhas | Separe tutorial (estavel) de campanha (datada). |
| Viaja na Milha | https://www.viajanamilha.com.br | Bonus e compra de milhas | Extraia origem, destino, %, teto, clube. Recalcule. |
| Farejador de Milhas | https://www.farejadordemilhas.com.br | Disponibilidade premio | Espaco, nao preco. Reconfirme no site da cia. Nao emite. |

Detalhe de cadencia e staleness: o JSON.

## Protocolo (obrigatorio)

Para qualquer post que citar um numero:

1. Anote a data do post. Bonus de transferencia com mais de 7 dias = stale. Alerta cash com mais de algumas horas = provavelmente morto.
2. Extraia: origem da moeda, destino, ratio, bonus %, bonus de clube, preco (se compra), validade, teto, restricoes.
3. Rode `calc_milheiro.py` com **esses** numeros. Cite o milheiro que voce calculou, nao o do blog.
4. Diga ao usuario para abrir Livelo/Esfera/Smiles/LATAM/Azul e ver se a campanha ainda esta no ar.
5. Nao copie "milheiro R$ 8,00" como fato. Se o blog nao mostra a conta, mostre a sua ou recuse o numero.

## O que nao fazer

- Nao scrape autenticado, nao login, nao emitir, nao transferir, nao comprar.
- Nao trate Farejador ou Seats.aero como inventario reservavel — e cache.
- Nao misture um alerta GRU-LIS com um voo NAT-LIS. Cote NAT, REC e FOR.
- Nao use este skill para "atualizar" `transfer-partners.json` com um bonus temporario. Bonus vai na conversa (e no calculo), ratio baseline fica no JSON.

## Quando a campanha nao esta no JSON de transfer-bonuses

O refresh semanal de `data/transfer-bonuses.json` cobre Amex/Chase/Citi/Cap One/Bilt. Livelo/Esfera **nao** entram la. Para BR, a fonte canonica e o post datado + o site da coalizao. Se nao conseguir verificar, diga "nao confirmei se o bonus ainda vale" em vez de inventar.

## Relacao com outros skills

- `milheiro` — a conta
- `brazil-loyalty` — quem transfere para quem
- `transfer-partners` — ratios baseline (incluindo as chaves BR)
- `seats-aero` / Farejador — espaco premio
- `lessons-learned` — nao filtrar programa na primeira busca
