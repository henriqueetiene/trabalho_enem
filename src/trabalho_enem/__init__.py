"""Médias do ENEM: regressões lineares por período, 2015–2025.

Gera 15 gráficos: para cada área, período completo (2015–2025),
pré-popularização (2015–2022) e pós-popularização (2023–2025).

Execução: trabalho-enem [--saida PASTA]
As 11 planilhas Sinopse ENEM AAAA.xlsx ficam na pasta do pacote.
Os resultados são gravados no diretório de execução por padrão.
"""
import argparse
from pathlib import Path
import posixpath
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent

ANOS = range(2015, 2026)
AREAS = {
    'Ciências da Natureza': '7.1.1',
    'Ciências Humanas': '7.2.1',
    'Linguagens, Códigos e suas Tecnologias': '7.3.1',
    'Matemática': '7.4.1',
    'Redação': '7.5.1',
}
PERIODOS = {
    '2015_2025': (2015, 2025),
    '2015_2022': (2015, 2022),
    '2023_2025': (2023, 2025),
}


def ler_medias_nacionais(caminho, abas):
    """Extrai a média nacional da célula D10 de cada aba especificada."""
    ns = {
        'm': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    }
    with zipfile.ZipFile(caminho) as z:
        raiz = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        caminhos = {rel.attrib['Id']: rel.attrib['Target'] for rel in rels}
        resultado = {}
        for sheet in raiz.findall('m:sheets/m:sheet', ns):
            nome = sheet.attrib.get('name')
            if nome not in abas:
                continue
            rid = sheet.attrib['{' + ns['r'] + '}id']
            alvo = caminhos[rid].lstrip('/')
            caminho_xml = alvo if alvo.startswith('xl/') else posixpath.normpath('xl/' + alvo)
            with z.open(caminho_xml) as f:
                for _, row in ET.iterparse(f, events=('end',)):
                    if row.tag != '{' + ns['m'] + '}row':
                        continue
                    n = int(row.attrib.get('r', 0))
                    if n == 10:
                        cel = next((c for c in row if c.attrib.get('r') == 'D10'), None)
                        if cel is not None and cel.attrib.get('t', 'n') != 'n':
                            raise ValueError(
                                f'Média deve ser uma célula numérica em '
                                f'{caminho.name}, aba {nome}, D10 '
                                f'(tipo: {cel.attrib["t"]})'
                            )
                        valor = cel.find('m:v', ns) if cel is not None else None
                        if valor is None or valor.text is None:
                            raise ValueError(f'Média não encontrada em {caminho.name}, aba {nome}, D10')
                        resultado[nome] = float(valor.text)
                        break
                    row.clear()
        faltam = set(abas) - set(resultado)
        if faltam:
            raise ValueError(f'Abas ausentes em {caminho.name}: {sorted(faltam)}')
        return resultado


def carregar_dados():
    registros = []
    for ano in ANOS:
        arquivo = PASTA / f'Sinopse ENEM {ano}.xlsx'
        if not arquivo.is_file():
            raise FileNotFoundError(f'Arquivo não encontrado: {arquivo}')
        medias = ler_medias_nacionais(arquivo, set(AREAS.values()))
        for area, aba in AREAS.items():
            media = medias[aba]
            if not np.isfinite(media):
                raise ValueError(f'Média inválida: {arquivo.name}, aba {aba}')
            registros.append({'Ano': ano, 'Área': area, 'Média': media})
    return pd.DataFrame(registros)


def gerar_grafico(serie, area, aba, inicio, fim, saida):
    x = serie['Ano'].to_numpy(dtype=float)
    y = serie['Média'].to_numpy(dtype=float)
    if len(x) < 2:
        raise ValueError(f'Período {inicio}–{fim} com menos de dois anos em {area}')

    # Ano relativo ao início do intervalo: mantém intercepto compreensível.
    inclinacao, intercepto = np.polyfit(x - inicio, y, 1)
    anos_linha = np.linspace(inicio, fim, 200)
    medias_previstas = inclinacao * (anos_linha - inicio) + intercepto

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.scatter(x, y, s=85, color='#2166ac', label='Média nacional observada', zorder=3)
    ax.plot(anos_linha, medias_previstas, color='#e58b30', linewidth=2.5,
            label='Regressão linear')
    # Mostrar marcador histórico apenas no gráfico que cobre ambos os períodos.
    if inicio < 2023 <= fim:
        ax.axvline(2022.5, linestyle='--', linewidth=1.5, color='#b34740',
                   label='Transição 2022/2023')
    for ano, media in zip(x, y):
        ax.annotate(f'{media:.1f}'.replace('.', ','), (ano, media),
                    xytext=(0, 9), textcoords='offset points', ha='center', fontsize=8)
    ax.set_title(f'ENEM — {area}\nMédia nacional e regressão linear ({inicio}–{fim})', fontsize=13)
    ax.set_xlabel('Ano')
    ax.set_ylabel('Média nacional (pontos)')
    ax.set_xticks(list(range(inicio, fim + 1)))
    ax.set_xlim(inicio - .35, fim + .35)
    margem = max(np.ptp(y) * .25, 8)
    ax.set_ylim(y.min() - margem, y.max() + margem)
    ax.grid(alpha=.24)
    sinal = '+' if inclinacao >= 0 else '−'
    ax.text(.02, .03,
            f'Inclinação: {sinal}{abs(inclinacao):.2f} pontos/ano'.replace('.', ','),
            transform=ax.transAxes, va='bottom', fontsize=10,
            bbox={'facecolor': 'white', 'alpha': .93, 'edgecolor': '#cccccc'})
    ax.legend(loc='best', fontsize=9)
    fig.tight_layout()
    area_normalizada = unicodedata.normalize('NFKD', area).encode('ascii', 'ignore').decode('ascii')
    nome_area = re.sub(r'[^a-z0-9]+', '_', area_normalizada.lower()).strip('_')
    nome = f'grafico_{nome_area}_{inicio}_{fim}.png'
    fig.savefig(saida / nome, dpi=180)
    plt.close(fig)
    return inclinacao


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0]) # type: ignore
    parser.add_argument(
        '--saida', type=Path, default=Path('graficos_enem_por_periodo'),
        help='Pasta de resultados (padrão: ./graficos_enem_por_periodo).',
    )
    saida = parser.parse_args(argv).saida
    dados = carregar_dados()
    saida.mkdir(parents=True, exist_ok=True)
    dados.to_csv(saida / 'medias_enem_2015_2025.csv', sep=';', decimal=',',
                 index=False, encoding='utf-8-sig')
    resultados = []
    for area, aba in AREAS.items():
        for inicio, fim in PERIODOS.values():
            serie = dados.loc[(dados['Área'] == area) &
                              dados['Ano'].between(inicio, fim)].sort_values('Ano')
            inclinacao = gerar_grafico(serie, area, aba, inicio, fim, saida)
            resultados.append({'Área': area, 'Período': f'{inicio}–{fim}',
                               'Inclinação (pontos/ano)': inclinacao})
            print(f'{area} | {inicio}–{fim} | Inclinação: {inclinacao:+.2f} pontos/ano')
    pd.DataFrame(resultados).to_csv(saida / 'inclinacoes_enem_por_periodo.csv',
                                    sep=';', decimal=',', index=False, encoding='utf-8-sig')
    print(f'\n15 gráficos e 2 arquivos CSV disponíveis em: {saida.resolve()}')


if __name__ == '__main__':
    main()
