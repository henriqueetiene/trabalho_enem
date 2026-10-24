import contextlib
import importlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import trabalho_enem as enem


class LeituraTests(unittest.TestCase):
    def test_tipos_de_celula(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'exemplo.xlsx'
            for tipo in (None, 'n', 's', 'inlineStr', 'str', 'b', 'e'):
                with self.subTest(tipo=tipo):
                    atributo = '' if tipo is None else f' t="{tipo}"'
                    with zipfile.ZipFile(arquivo, 'w') as z:
                        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="7.1.1" r:id="rId1"/></sheets></workbook>')
                        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                        # Um shared string com índice 0 não pode virar média 0.
                        z.writestr('xl/sharedStrings.xml', '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>499.9</t></si></sst>')
                        valor = '499.9' if tipo in (None, 'n') else '0'
                        z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="10"><c r="D10"{atributo}><v>{valor}</v></c></row></sheetData></worksheet>')
                    if tipo in (None, 'n'):
                        self.assertEqual(enem.ler_medias_nacionais(arquivo, {'7.1.1'}), {'7.1.1': 499.9})
                    else:
                        with self.assertRaisesRegex(ValueError, 'exemplo.xlsx, aba 7.1.1, D10'):
                            enem.ler_medias_nacionais(arquivo, {'7.1.1'})


class SaidaTests(unittest.TestCase):
    def test_importacao_sem_criar_diretorios(self):
        with patch.object(Path, 'mkdir', side_effect=PermissionError('sem escrita')):
            importlib.reload(enem)

    def test_execucao_com_destino_personalizado(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / 'resultados' / 'enem'
            with contextlib.redirect_stdout(io.StringIO()):
                enem.main(['--saida', str(saida)])
            self.assertEqual(len(list(saida.glob('*.png'))), 15)
            medias = enem.pd.read_csv(saida / 'medias_enem_2015_2025.csv', sep=';', decimal=',')
            inclinacoes = enem.pd.read_csv(saida / 'inclinacoes_enem_por_periodo.csv', sep=';', decimal=',')
            self.assertEqual(len(medias), 55)
            self.assertEqual(len(inclinacoes), 15)


if __name__ == '__main__':
    unittest.main()
