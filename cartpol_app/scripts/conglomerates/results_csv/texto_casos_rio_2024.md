# Estudos de caso comparativos: o índice fuzzy de concentração × LQ × HC × LISA

**Dados:** eleição municipal de 2024, cargo de vereador, município do Rio de Janeiro (TSE, votação por seção agregada em 152 bairros com votos; malha de vizinhança por contiguidade sobre 160 bairros, IBGE 2022). Quociente Eleitoral QE = 59.154; total de votos nominais válidos = 2.851.844; limiar de significância do Filtro 1 = 5%·QE / 152 ≈ 19,5 votos por bairro. Perfis computados para 865 candidatos (ver *dot plot*).

**Nota metodológica (LISA).** O Moran local (Anselin, 1995) foi calculado sobre os votos absolutos do candidato por bairro, com matriz de pesos de contiguidade (*queen/touches*) padronizada por linha, sobre o universo dos 160 bairros (bairros sem voto entram com valor zero). A inferência usa 999 permutações condicionais com semente fixa (pseudo-p; α = 0,05); o Moran global usa permutação irrestrita do vetor. Implementação própria em `lisa_moran.py`, sem dependências externas.

---

## Caso 1 — Nosso índice × LQ: Carlo Caiado (PSD, 47.423 votos, eleito)

**Perfil espacial.** Carlo Caiado, um dos vereadores mais votados da cidade, obteve votos em 151 dos 152 bairros, com desempenho forte em toda a orla oeste — da Barra da Tijuca a Guaratiba — e presença relevante em Jacarepaguá.

**O que o LQ reporta.** O Location Quotient atinge seu máximo em **Pedra de Guaratiba (LQ = 18,87)**, seguido de Vargem Grande (7,09) e Guaratiba (6,73). O bairro em que o candidato mais votou — **Barra da Tijuca, 5.183 votos — aparece apenas em 7º lugar (LQ = 4,78)**, atrás inclusive de **Camorim (LQ = 4,88), onde o candidato obteve somente 70 votos**. Ao todo, 27 bairros apresentam LQ > 1.

**Por que isso é enganoso.** O LQ é uma razão de participações: divide a fatia local do candidato pela sua fatia global. Em bairros pequenos, o denominador diminui e a razão infla — um punhado de votos em Camorim "vale" mais, em LQ, do que milhares na Barra da Tijuca. O resultado é um ranqueamento que não corresponde à importância real de cada bairro para a votação do candidato: seguindo o LQ, o "reduto" de Caiado seria Pedra de Guaratiba; seguindo o HC, seria Guaratiba (HC = 4.389); seguindo os votos brutos, a Barra da Tijuca. **Três métricas, três redutos diferentes** — e nenhuma delas emite um juízo sobre o perfil do candidato como um todo.

**O que o nosso algoritmo reporta.** Após a filtragem (122 bairros significativos), o algoritmo identifica que praticamente toda essa região é **um único conglomerado contíguo de 114 bairros, que concentra 98,3% dos votos do candidato** (RUESP_CAN = 0,983), mais um fragmento menor (8 bairros; 1,0%). O índice final é **0,348 (baixa concentração)**: um candidato de base ampla e espacialmente coesa, não um candidato de reduto. A aparente contradição entre os três "redutos" dos índices clássicos se dissolve — eles são partes do mesmo território contíguo, que o algoritmo trata como uma única unidade de análise.

**Conclusão do caso.** O LQ, tomado bairro a bairro, é instável em áreas pequenas e não converge para um diagnóstico; o nosso algoritmo integra os bairros em conglomerados contíguos e entrega um veredito único e coerente com a estrutura espacial real da votação. O caso se repete, de forma ainda mais nítida, com o segundo candidato mais votado da cidade, **Márcio Ribeiro (56.754 votos)**: seu LQ máximo ocorre em **Riachuelo (10,11), onde ele obteve 844 votos — quase sete vezes menos que na Tijuca (5.634 votos)**, seu verdadeiro centro de gravidade, com 67 bairros acesos em LQ > 1.

---

## Caso 2 — Nosso índice × HC: Marcelo Diniz (39.963 votos) versus Paulo Roberto (2.876 votos)

**Perfis espaciais.** Marcelo Diniz, eleito com quase 40 mil votos, espalha sua votação por 150 bairros, da Barra da Tijuca à Zona Norte. Paulo Roberto Ferreira de Souza, não eleito, obteve 2.876 votos — dos quais **92,4% em um único bairro, Santa Cruz** (2.658 votos).

**O que o HC reporta.** O Horizontal Cluster Index mede, em votos, o excedente do candidato em relação a uma distribuição homogênea. O HC positivo total de **Diniz soma 31.297 votos — o maior valor de toda a cidade —**, com pico de 13.417 em Jacarepaguá. O de **Paulo Roberto soma 2.555**. Lido como medida de concentração, o HC afirma que Diniz é **cerca de 12 vezes "mais concentrado"** que Paulo Roberto.

**Por que isso é enganoso.** O HC é expresso em votos absolutos e, portanto, **escala com o tamanho eleitoral do candidato**: um candidato 14 vezes maior produz excedentes proporcionalmente maiores em seus bons bairros, ainda que sua votação seja espacialmente difusa. O HC responde "quantos votos acima do esperado", não "quão concentrada é a votação" — duas perguntas que só coincidem quando os candidatos comparados têm portes semelhantes.

**O que o nosso algoritmo reporta.** A ordenação se inverte, corretamente. Paulo Roberto: um único conglomerado (Santa Cruz–Campo Grande–Paciência) com 95,1% dos votos → índice **0,878, muito alta** — o arquétipo do ultra-concentrador. Diniz: quatro conglomerados — o principal com 51 bairros (97% dos votos) e três fragmentos residuais — → índice **0,249, muito baixa, o menor entre os 51 eleitos**. Por ser construído sobre *proporções* (RUESP_CAN) e não sobre volumes, o índice é invariante ao porte do candidato e comparável entre candidatos de qualquer tamanho.

**Conclusão do caso.** O HC confunde tamanho com concentração; o nosso índice os separa. É exatamente o tipo de erro que compromete comparações entre candidatos — o uso mais comum desses indicadores na literatura.

---

## Caso 3 — Nosso índice × LISA: Rafael Aloisio Freitas (40.875 votos) versus Paulo Roberto (2.876 votos)

**Perfis espaciais.** Rafael Aloisio Freitas, eleito com 40,9 mil votos, tem apoio amplo e suavemente decrescente a partir do Grande Méier. Paulo Roberto, como visto, é o ultra-concentrador: 92,4% dos votos em Santa Cruz.

**O que o LISA reporta.** Para Rafael, o diagnóstico é vigoroso: **Moran global I = 0,429 (p = 0,001) — o maior da amostra —**, com o Méier em I local = 22,55 (p = 0,001) e um cluster High-High significativo de 12 bairros contíguos (Méier, Cachambi, Engenho de Dentro, Todos os Santos, Engenho Novo, Grajaú, Vila Isabel, Andaraí, entre outros). Para Paulo Roberto, o LISA praticamente silencia: **Moran global I = 0,008 (p = 0,272, não significativo)** e — o resultado mais eloquente — **o próprio reduto de Santa Cruz, com 92% dos votos, recebe I local = 0,03 com pseudo-p = 1,00**: estatisticamente indistinguível de aleatoriedade espacial. O único aglomerado que o método aponta é o vizinho Paciência, com 1 bairro.

**Por que isso é enganoso.** O Moran local mede **autocorrelação — a suavidade espacial dos valores —, não concentração**. Uma votação que decai gradualmente por uma região inteira (Rafael) gera vizinhanças homogêneas e I altíssimo; um pico solitário num único bairro (Paulo Roberto) tem vizinhos próximos de zero, de modo que o produto z·lag se anula — e o valor extremo ainda domina a variância global, achatando as estatísticas locais dos demais bairros. O resultado é um **ranking invertido em relação à concentração**: o candidato mais concentrado da cidade é o de *menor* estrutura LISA, e o candidato disperso de base regional é o de *maior*. Além disso, a LISA sofre nas mesmas situações-limite que motivam este trabalho: distribuições extremamente assimétricas e redutos de bairro único, exatamente os casos de maior interesse substantivo em geografia eleitoral.

**O que o nosso algoritmo reporta.** Rafael: conglomerado principal de 109 bairros com 98,5% dos votos, mais dois fragmentos → índice **0,300 (baixa)** — base ampla, não reduto. Paulo Roberto: **0,878 (muito alta)**. A ordenação volta a corresponder à noção substantiva de concentração, e o cluster HH que a LISA detecta para Rafael é um subconjunto do conglomerado que nosso algoritmo já identifica — com a vantagem de que o algoritmo o pondera dentro de um veredito global do candidato, em vez de reportá-lo isoladamente.

**Conclusão do caso.** A LISA responde "a distribuição é espacialmente suave?"; nosso índice responde "a votação é concentrada?". São perguntas diferentes, e é a segunda que interessa ao estudo de redutos eleitorais. Nos casos extremos — os mais relevantes — a LISA é cega por construção.

---

## Caso 4 (controle) — Convergência: Emerson de Souza Melo (7.942 votos)

Para verificar que as divergências acima refletem falhas dos indicadores clássicos, e não idiossincrasia do nosso método, examinamos um caso inequívoco. Emerson de Souza Melo obteve 75% de seus votos em **Vila Kennedy** (5.976 de 7.942). Aqui **todos os métodos concordam**: o LQ máximo é 102,08 em Vila Kennedy (o reduto correto, com apenas 2 bairros em LQ > 1); o HC máximo é 5.917, também em Vila Kennedy; a LISA marca Vila Kennedy como High-High significativo (I = 30,78; p = 0,009), com Moran global 0,226 (p = 0,001); e o nosso algoritmo identifica um único conglomerado de 9 bairros com 96,3% dos votos, índice **0,802 (alta)**. Quando o padrão espacial é claro, o nosso índice converge com a literatura — as divergências dos casos 1–3 ocorrem precisamente onde cada indicador clássico apresenta sua fragilidade estrutural.

---

## Síntese

| Fragilidade estrutural | LQ | HC | LISA | Nosso índice |
|---|---|---|---|---|
| Instável em bairros pequenos (ranqueia errado o reduto) | ✗ falha (Caiado, Márcio Ribeiro) | — | — | ✓ conglomerados contíguos |
| Confunde porte do candidato com concentração | — | ✗ falha (Diniz ×12 Paulo) | — | ✓ proporções, invariante a escala |
| Cego a redutos de pico único (assimetria extrema) | — | — | ✗ falha (Paulo: p=1,00 no reduto) | ✓ valor máximo no ultra-concentrador |
| Emite veredito no nível do candidato | ✗ (por bairro) | ✗ (por bairro) | ✗ (por bairro) | ✓ escore único ∈ [0,1] + rótulo |
| Converge no caso inequívoco (Emerson) | ✓ | ✓ | ✓ | ✓ |

Em conjunto, os casos mostram que os indicadores clássicos falham em direções diferentes — o LQ por instabilidade da razão em unidades pequenas, o HC por escalar com o volume, a LISA por medir suavidade em vez de concentração — enquanto o índice proposto, ao combinar filtragem ancorada no QE, agregação por contiguidade espacial e inferência fuzzy interpretável, produz um veredito único, comparável entre candidatos de qualquer porte e alinhado, caso a caso, à leitura substantiva dos mapas. O *dot plot* dos 865 candidatos com perfil computável posiciona os casos analisados ao longo de todo o espectro de concentração, ilustrando a capacidade discriminante do índice.

---

### Arquivos de suporte
- `caso_lq_carlo_caiado.csv`, `caso_hc_diniz_vs_paulo.csv`, `caso_lisa_rafael_vs_paulo.csv`, `caso_controle_emerson.csv` — mini-tabelas por caso.
- `json/lisa_<nr>_<slug>.json` — LISA completo por bairro (I, quadrante, pseudo-p) dos seis candidatos.
- `dotplot_concentracao_rio_2024.png` — distribuição do índice para os 865 candidatos, casos rotulados.
- `casos_baselines_dados.json` — todos os números citados neste texto.
