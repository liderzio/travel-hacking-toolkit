---
name: brazil-loyalty
description: Programas brasileiros de milhas e pontos. Smiles GOL, LATAM Pass, Azul Fidelidade TudoAzul, Livelo, Esfera, Itau Iupp, Nubank Ultravioleta, Santander Esfera, C6 Atomos, Inter Loop, clubes e ratios de transferencia para TAP, Iberia, Qatar Privilege Club, AAdvantage. Load on any Brazilian points, milhas, Livelo, Smiles, LATAM Pass, Azul, or bank-points question.
category: loyalty
summary: Programas BR de milhas e pontos, clubes e mapa de transferencia. Ratios baseline, bonus sempre a verificar.
api_key: None (local data)
---

# Fidelidade brasileira

**Dados:** `data/brazil-loyalty.json` (programas, clubes, aeroportos NAT/REC/FOR) e `data/transfer-partners.json` (ratios).

Este skill ensina o agente a raciocinar com o ecossistema BR. Nao substitui a calculadora (`milheiro`) nem as fontes de promo (`brazil-deals`).

## Moedas transferiveis (o que o usuario "tem")

Trate cada uma como Chase UR no toolkit original: o saldo efetivo em Smiles/LATAM/Azul e o saldo direto **mais** o que der para transferir.

| Chave | Nome | Destinos baseline (1:1, verificar) |
|-------|------|--------------------------------------|
| `livelo` | Livelo | Smiles, LATAM Pass, Azul, TAP, Iberia, Qatar Avios, AAdvantage, Flying Blue, Emirates, LifeMiles, Etihad, Air Europa, Accor (ratio Accor costuma ser pior que 1:1) |
| `esfera` | Esfera (Santander) | Smiles, LATAM Pass, Azul, TAP, Accor, outros — confirmar no Esfera |
| `iupp` | Itau Iupp | Smiles, LATAM Pass, Azul; as vezes Livelo |
| `nubank` | Nubank Rewards / Ultravioleta | Smiles, LATAM Pass, Azul, Livelo, Accor |
| `c6_atomos` | C6 Atomos | Smiles, LATAM Pass, Azul, TAP, Livelo, Accor |
| `inter_loop` | Inter Loop | Smiles, LATAM Pass, Azul, Livelo |

**Ratio 1:1 e o baseline, nao a oferta.** O valor esta no bonus de transferencia. Sempre rode `transfer-bonuses` (EUA) **e** `brazil-deals` (BR). Se o arquivo de bonus EUA nao tiver Livelo, isso e esperado — cace a campanha nas fontes BR e recalcule com `milheiro transfer`.

Nao invente um parceiro que nao esta em `data/transfer-partners.json`. Se o usuario disser que um caminho existe e o arquivo nao tem, verifique no site da coalizao **com o usuario** (voce nao loga) e so entao atualize o JSON.

## Programas aereos

| Chave | Programa | Alianca | Seats.aero | Melhor uso tipico saindo do Nordeste |
|-------|----------|---------|------------|--------------------------------------|
| `smiles` | Smiles (GOL) | nenhuma | `smiles` | GOL domestico; AF/KLM Europa; posicionar NAT→GRU |
| `latam_pass` | LATAM Pass | saiu da oneworld | pode faltar | Metal LATAM na America do Sul; Delta via parceria; GRU/GIG |
| `azul` | Azul Fidelidade | nenhuma | `azul` | Malha Azul no Nordeste; TAP via LIS; United em alguns trechos |

Parceiros listados em `data/partner-awards.json` e `data/brazil-loyalty.json` sao o cache. O site da cia e a fonte da verdade.

## Clubes

Clube Smiles, Clube Livelo, Clube LATAM Pass, Clube Azul creditam milhas/pontos todo mes e quase sempre dao **percentual extra** em compra ou transferencia.

- Estrutura dos planos (1000/2000/5000...): `data/brazil-loyalty.json` → `clubs`
- Preco: o usuario informa. Sempre. A calculadora recusa default.
- Empilhamento: bonus de clube + bonus de campanha, modo `additive`, salvo regulamento

Nao assine clube pelo usuario. Nao diga "o Clube X custa R$ Y" a menos que o usuario (ou um post datado de hoje) tenha acabado de citar Y.

## Reachability

Quando o Seats.aero mostrar `smiles` ou `azul`:

1. Saldo direto no programa?
2. Caminho em `transfer-partners.json` a partir de Livelo, Esfera, Iupp, Nubank, C6, Inter?
3. Bonus vigente? (`brazil-deals` + calculadora)
4. Se nao houver cache Seats.aero para LATAM Pass, busque latam.com. Nao declare morto.

Programas internacionais uteis a partir de Livelo (quando o parceiro estiver ativo): TAP Miles&Go (REC/FOR→LIS), Iberia Plus (Avios), Qatar Privilege Club (Qsuites via GRU), AAdvantage (oneworld). Confirme o parceiro no Livelo antes de recomendar o caminho.

## Holds e transferencia

Smiles, LATAM Pass e Azul **nao** tem hold publico no estilo AA 24h. A regra "segura o asento, depois transfere" quase nao existe aqui.

- Oriente o usuario a abrir a tarifa premio no site da cia **e so entao** transferir.
- Transferencias Livelo/Esfera costumam cair em minutos, mas sao irreversiveis.
- Este toolkit **nao transfere**. Voce descreve os passos; o usuario executa no site.

## Aeroportos

Padrao deste fork: **NAT**. Sempre cotar **REC** e **FOR**. Long-haul: posicionar via GRU/GIG/BSB se o premio nao partir do Nordeste. TAP Lisboa e historicamente mais REC/FOR do que NAT — confirme em Wikipedia (`wikipedia-airports`) antes de dizer que a rota existe.

## Idioma e moeda

Resposta ao usuario em **pt-BR**. Precos em **BRL**. Metrica de pontos: **milheiro**, nao so cpp. Cpp USD fica como complemento para programas americanos.

## Proibido

Nada neste skill autoriza login, scraping autenticado, compra de milhas, emissao ou transferencia. American Airlines Docker login **nao** tem equivalente BR — nao crie um.
