# Análise das médias do ENEM (2015–2025)

Projeto de probabilidade e estatística que analisa a evolução das médias nacionais do ENEM nas cinco áreas: Ciências da Natureza, Ciências Humanas, Linguagens, Matemática e Redação.

O script ajusta regressões lineares para cada área em três intervalos: **2015–2025**, **2015–2022** e **2023–2025**. A inclinação da reta representa a tendência de variação da média, em pontos por ano.

## Requisitos

- Python 3.14 ou superior.
- Dependências declaradas em `pyproject.toml`: Matplotlib, NumPy, pandas e openpyxl.
- As 11 planilhas `Sinopse ENEM AAAA.xlsx`, de 2015 a 2025, dentro de `src/trabalho_enem/`.

## Execução

Na raiz do projeto, usando o gerenciador de pacotes uv:

```bash
uv sync
uv run trabalho-enem
```

Como alternativa, instale e execute com pip:

```bash
python -m pip install -e .
trabalho-enem
```

## Dados de entrada

As planilhas de sinopse do ENEM foram baixadas do site oficial do Inep, na página [Sinopses Estatísticas do Enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/enem), em **20 de outubro de 2026**.

O script lê diretamente o XML interno das planilhas Excel e extrai a célula **D10** das seguintes abas, assumindo que ela contém a média nacional:

| Área | Aba |
| --- | --- |
| Ciências da Natureza | `7.1.1` |
| Ciências Humanas | `7.2.1` |
| Linguagens, Códigos e suas Tecnologias | `7.3.1` |
| Matemática | `7.4.1` |
| Redação | `7.5.1` |

A execução é interrompida se faltar uma planilha, uma aba ou uma média válida. Arquivos CSV não são usados como entrada.

## Resultados

Os arquivos são gerados em `src/trabalho_enem/graficos_enem_por_periodo/`:

- **15 gráficos PNG**: um para cada combinação de área e período, com as médias observadas, a regressão linear e sua inclinação. Exemplo: `grafico_matematica_2015_2025.png`.
- **`medias_enem_2015_2025.csv`**: 55 registros com ano, área e média nacional.
- **`inclinacoes_enem_por_periodo.csv`**: inclinações das 15 regressões, em pontos por ano.

Os CSVs usam ponto e vírgula como separador, vírgula decimal e codificação UTF-8 com BOM. As inclinações também são exibidas no terminal. Os gráficos são salvos sem abrir janelas.

A pasta de resultados é ignorada pelo Git e pode ser recriada executando o projeto.

## Interpretação

Inclinações positivas indicam tendência de crescimento das médias; negativas indicam queda. Os gráficos do período completo marcam a transição entre 2022 e 2023.

A análise é descritiva: não calcula correlação de Pearson, R² ou significância estatística e não demonstra relações de causa e efeito. O intervalo 2023–2025 contém apenas três observações por área.
