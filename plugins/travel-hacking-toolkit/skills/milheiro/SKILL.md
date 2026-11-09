---
name: milheiro
description: Calcula custo e valor do milheiro em BRL para compra de milhas, clubes (Smiles, Livelo, LATAM, Azul), bonus de transferencia e resgate. Use when the user asks custo do milheiro, milheiro, compra de milhas, bonus Livelo/Esfera, Clube Smiles, Clube Livelo, Clube LATAM, Clube Azul, or whether a Brazilian points purchase/transfer is cheap.
category: loyalty
summary: Custo do milheiro em BRL. Compra, clube, bonus de transferencia e resgate. Precos sao sempre input, nunca fato.
api_key: None (free, local data)
---

# Calculadora de milheiro

Converte qualquer oferta brasileira (compra de milhas, clube, transferencia com bonus) no **custo do milheiro em BRL** — reais por 1.000 milhas creditadas — e compara com o **valor do milheiro** de um premio vs a tarifa cash.

**Nao precisa de API.** Nao acessa conta, nao compra, nao transfere.

**Regra de ouro:** todo preco e um input do usuario ou de um post DATADO. Este skill nao tem tabela de mensalidade de clube. Se o usuario nao informou o preco, peca o numero e pare. Nao invente.

## Formula

```
custo_do_milheiro = total_pago_BRL * 1000 / milhas_creditadas
```

Bonus no Brasil quase sempre **somam** (banner "80% + 30% clube" = 110%). Padrao da ferramenta: `--bonus-mode additive`. Use `multiplicative` so se o regulamento disser que um bonus incide sobre o outro.

## CLI

```bash
# Compra de milhas (numeros ilustrativos — nao sao oferta vigente)
python3 skills/milheiro/scripts/calc_milheiro.py purchase \
  --price 270 --miles 10000 --bonus-pct 80 --club-bonus-pct 30 --json

# Clube: o usuario OBRIGA-SE a informar a mensalidade vigente
python3 skills/milheiro/scripts/calc_milheiro.py club \
  --monthly-fee 00.00 --monthly-miles 1000 --months 12 --extra-miles 0 --json

# Transferencia Livelo/Esfera/banco -> cia
python3 skills/milheiro/scripts/calc_milheiro.py transfer \
  --source-milheiro 14 --ratio 1 --bonus-pct 100 --club-bonus-pct 40 --json

# Valor do milheiro de um premio (cash evitado / milhas)
python3 skills/milheiro/scripts/calc_milheiro.py redeem \
  --cash 1800 --taxes 90 --miles 20000 --json

# Decisao pontos vs cash
python3 skills/milheiro/scripts/calc_milheiro.py compare --custo 15 --valor 45 --json
```

## Quando usar

- "Essa compra de Smiles esta barata?"
- "Quanto fica o milheiro do Clube Livelo 5.000?"
- "Livelo com 80% + clube 40% para Azul, vale?"
- "Melhor comprar milha ou transferir Livelo?"
- Qualquer post de Passageiro de Primeira / Viaja na Milha / Pontos pra Voar com tabela de milheiro

## Fluxo

1. Extraia do usuario ou do post: preco, milhas-base, bonus %, bonus de clube %, taxas.
2. Rode a CLI. Nao calcule de cabeca se houver clube + campanha — o modo additive vs multiplicative muda o resultado.
3. Rotule com as faixas heuristicas (excepcional / bom / ok / fraco / ruim) de `data/brazil-loyalty.json` → `acquisition_heuristics`. Diga que e heuristica, nao valuacao publicada.
4. Se houver tarifa cash do mesmo trecho, rode `redeem` + `compare`.
5. Mostre a conta em tabela. Deixe claro que o usuario confirma no site do programa **antes** de gastar dinheiro ou pontos.
6. Nao ofereca executar a compra ou a transferencia.

## Saida

Sempre tabela. Exemplo de colunas:

| Cenario | Pago (BRL) | Milhas creditadas | Milheiro | Selo |
|---------|------------|-------------------|----------|------|
| Compra 10k + 80% | 270 | 18.000 | R$ 15,00 | bom |
| Mesma compra + 30% clube (additive) | 270 | 21.000 | R$ 12,86 | excepcional |

Depois da tabela: uma recomendacao em uma frase ("transfere Livelo nesta campanha; o milheiro efetivo fica abaixo do clube avulso") e o aviso de confirmar no site.

## Empilhamento de clube

| Clube | O que o usuario precisa informar | Como entra na conta |
|-------|----------------------------------|---------------------|
| Clube Smiles | mensalidade vigente, milhas/mes, bonus extra de compra/transferencia do plano | `club` para a assinatura; `--club-bonus-pct` na compra/transferencia |
| Clube Livelo | mensalidade, pontos/mes, % extra na transferencia | idem; o % extra vai em `--club-bonus-pct` no subcomando `transfer` |
| Clube LATAM Pass | mensalidade, pontos/mes, % extra na compra | `club` + `purchase` |
| Clube Azul | mensalidade, pontos/mes, % extra na compra | `club` + `purchase` |

Estrutura dos planos (1000/2000/5000...): `data/brazil-loyalty.json` → `clubs`. Sem precos.

## Relacao com CPP

Milheiro (R$/1.000) e a metrica padrao no Brasil. CPP em USD centavos e secundario. Para um usuario NAT, mostre milheiro primeiro. O skill `points-valuations` continua valido para programas americanos; para Smiles/LATAM/Azul/Livelo use esta ferramenta.

Conversao aproximada so se o usuario pedir cpp: `cpp_usd ≈ (milheiro_BRL / 10) / cambio_USD`. Nao misture as duas unidades na mesma coluna.

## Proibido

- Logar em Smiles, LATAM, Azul, Livelo, Esfera, Itau, Nubank, C6, Inter
- Comprar milhas, assinar clube, transferir pontos ou emitir passagem
- Reusar mensalidade de um post antigo como default
- Tratar o milheiro publicado num blog como fato — recalcule
