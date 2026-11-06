# Simulado Rank 06 no terminal

Treino local com 9 exercícios em 2 níveis, obtidos de [42exam.net](https://rank06.42exam.net/) em 06/11/2026. O site é comunitário; este corretor não é o avaliador oficial da 42. Implementação baseada no simulador Rank-04 local, commit baee48e.

## Abrir

Linux e Python 3.10 ou superior; somente biblioteca padrão.

```bash
cd /home/silva/main/Exam-Rank-06
python3 -B main.py
```

1. **Praticar:** escolher qualquer exercício, sem prazo, com detalhes da primeira falha.
2. **Iniciar simulado:** quatro horas corridas; sortear um exercício por nível, na ordem. Só aprovação libera o seguinte.
3. **Sair:** fechar o programa.

O total da prova é 2 exercícios, um por nível, conforme a organização do site. A pontuação é proporcional aos níveis aprovados, até 100. O prazo de quatro horas reproduz o treino do Rank-04 e não certifica o tempo oficial do exame.

## Entregar

Escreva em `rendu/` o arquivo indicado no terminal. Implemente todas as funções ou métodos apresentados, com os nomes exatos; só imprimir resultados não atende ao contrato. Salve no editor e digite `corrigir` ou `grademe` no simulado.

Após corrigir, a tela mostra **✅ correto** ou **❌ incorreto**, com `Progresso: 1/2`, por exemplo. Acerto limpa o enunciado anterior e apresenta o próximo automaticamente. Erro mantém o nível. Na prática, aparece também o primeiro diagnóstico. As cores e a limpeza de tela são desativadas quando a saída é redirecionada; `NO_COLOR` desativa as cores.

| Comando | Ação |
| --- | --- |
| `corrigir` / `grademe` | Testar a entrega salva. |
| `enunciado` | Reler a questão atual. |
| `status` | Consultar etapa, tentativas e tempo. |
| `sair` | Voltar ao menu, preservando os arquivos. |
| `encerrar` | Encerrar a tentativa com o progresso atual. |

## Reinício e arquivos

Cada início cria uma tentativa nova: sorteio, progresso zerado e quatro horas. A `rendu/` anterior inteira, inclusive ocultos e subpastas, é movida para `historico/<identificador>/rendu/`. O estado é arquivado separadamente. Praticar também cria uma tentativa limpa após a seleção. Não há retomada automática.

```text
main.py                         entrada
src/                            simulador, corretor, testes e documentação
src/subjects.json               catálogo e exemplos da fonte consultada
gabarito/enunciados/level-*/     enunciados originais em inglês
gabarito/level-*/                soluções de referência compactas
rendu/                          somente suas entregas
src/.session.json               estado da tentativa atual
historico/                      tentativas anteriores
```

Enunciado aparece somente no terminal; rendu começa vazia. Entregas, histórico e estado não entram no Git. O gabarito é acessível para revisão, mas não é copiado para sua entrega.

## Exercícios

| Nível | Arquivo |
| --- | --- |
| 1 | `pack_strings.py` |
| 1 | `prefix_dictionary.py` |
| 1 | `redundant_link.py` |
| 1 | `task_order.py` |
| 1 | `trie_autocomplete.py` |
| 2 | `bridge_finder.py` |
| 2 | `cache_keeper.py` |
| 2 | `min_heap.py` |
| 2 | `union_find_system.py` |

## Critérios locais e ambiguidades da fonte

- O segundo exemplo de CacheKeeper no site contradiz a regra LRU: após inserir (1, 1), (2, 2), (3, 3), com capacidade 2, get(2) retorna **2**, e não -1. O texto original foi preservado; o teste segue a regra escrita. Capacidade sempre positiva.
- Pack/unpack aceita qualquer formato de serialização que retorne str e reconstrua exatamente a lista original, inclusive strings vazias, dígitos, delimitadores, Unicode e quebras de linha.
- UnionFind aceita qualquer raiz válida em empates. A bateria verifica conectividade e representantes, sem exigir o nome de atributos internos.
- Prefixo vazio corresponde a qualquer palavra já inserida; o dicionário vazio retorna False.
- Bridges usa grafos simples e simétricos, sem arestas paralelas. As tuplas e sua ordem são verificadas.


Os esclarecimentos pertinentes também aparecem no terminal. Os enunciados e exemplos originais permanecem preservados nos .txt e em src/subjects.json; os critérios locais não são apresentados como regras oficiais.

## Correção e limites

A bateria inclui exemplos e casos adicionais determinísticos, com resultados calculados independentemente das soluções de referência. Classes são testadas por sequências de operações; exercícios com duas funções testam ambas. O retorno é comparado também por tipo, incluindo tuplas, listas e bool. Respostas válidas não únicas são avaliadas pelo contrato, quando aplicável.

Cada entrega roda em processo separado, com até cinco segundos de parede, três segundos de CPU e 512 MiB de memória. O prazo restante da prova também limita a correção. Há checagem estática de recursos proibidos declarados no site, incluindo aliases comuns; essa checagem não cobre todas as formas dinâmicas de importação.

A aprovação vale para esta bateria; não prova correção universal nem complexidade ótima. Estruturas e otimizações exigidas, como trie, compressão de caminho, união por rank e custo das operações, também requerem leitura do código. Os gabaritos implementam essas estruturas. O isolamento evita travamentos comuns e não constitui barreira de segurança para código malicioso.

## Conferir o material antes do estudo

**Regra explícita do usuário, 06/11/2026:** antes de começar ou retomar o estudo deste rank, consultar https://rank06.42exam.net/ e comparar questões, níveis, arquivos, assinaturas, exemplos, restrições e enunciados com a cópia local. Os dados da página ficam em `js/data.js`; a versão recuperada está em `src/subjects.json`.

Se houver divergência, informar as mudanças e preservar suas tentativas/soluções antes de atualizar o material e os testes. Se o site estiver inacessível, registrar a limitação e não afirmar que o conteúdo continua igual. A regra também está na memória permanente; o programa não consulta a internet automaticamente.

## Verificar o programa

```bash
python3 -B -m unittest discover -s src/tests -v
```

Os testes usam diretórios temporários e não iniciam uma tentativa na sua pasta de trabalho.
