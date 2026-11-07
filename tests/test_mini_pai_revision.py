from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from openpyxl import load_workbook
import mini_pai_confirmar as confirmar
import mini_pai_exportar as exportar
import mini_pai_revision as revision
import mini_pai_seleccionar as selector
from tests import test_mini_pai_confirmar as ejemplos


class PruebasRevisionUsuario(unittest.TestCase):
    def setUp(self):
        self.ejemplo = ejemplos.PruebasConfirmaciones()
        self.datos = self.ejemplo.entrada()

    def manual(self, datos=None, **cambios):
        decision = dict(self.ejemplo.decisiones()[0], IdCodigo=None, **cambios)
        conexion = Mock()
        salida = confirmar.confirmar(datos or self.datos, [decision], conexion)
        conexion.cursor.assert_not_called()
        return salida

    def test_codigo_final_no_admite_descripciones_distintas_incluyendo_originales(self):
        for matriz in (False, True):
            for mismo_texto in (False, True):
                with self.subTest(matriz=matriz, mismo_texto=mismo_texto):
                    datos = deepcopy(self.datos)
                    if matriz:
                        datos = confirmar.confirmar(datos, self.ejemplo.decisiones(), self.ejemplo.conexion(datos))
                        codigo = 'CB-001'
                        descripcion = datos['busquedas_construbase'][0]['seleccion']['catalogo']['DescripcionLarga']
                    else:
                        datos['busquedas_construbase'][0].update(candidatos=[], estado='sin_candidatos_en_busqueda')
                        codigo = datos['registros'][2]['clave']
                        descripcion = datos['registros'][2]['descripcion']
                    otro = dict(datos['registros'][2], fila=4, clave=codigo,
                                descripcion=descripcion if mismo_texto else 'Otra descripción completa')
                    datos['registros'].append(otro)
                    datos['busquedas_construbase'].append(dict(hoja='Obra', fila=4, seleccion=None,
                                                              candidatos=[], estado='sin_candidatos_en_busqueda'))
                    if mismo_texto:
                        libro = exportar.crear_excel(datos, final=True)
                        self.assertEqual(libro['Catálogo']['B4'].value, libro['Catálogo']['B5'].value)
                        libro.close()
                    else:
                        with self.assertRaisesRegex(ValueError, 'Código.*descripciones'):
                            exportar.crear_excel(datos, final=True)
                        with tempfile.TemporaryDirectory() as carpeta:
                            entrada, salida = Path(carpeta)/'entrada.json', Path(carpeta)/'salida.xlsx'
                            entrada.write_text(json.dumps(datos), encoding='utf-8')
                            with patch('sys.argv', ['exportar', str(entrada), '--final', '--salida', str(salida)]):
                                with self.assertRaisesRegex(ValueError, 'Código.*descripciones'):
                                    exportar.main()
                            self.assertFalse(salida.exists())
                            self.assertFalse(salida.with_suffix('.md').exists())

    def test_original_sin_matriz_auditoria_excel_y_reporte(self):
        antes = deepcopy(self.datos)
        datos = self.manual()
        self.assertEqual(self.datos, antes)
        libro = exportar.crear_excel(datos, final=True)
        self.addCleanup(libro.close)
        r = self.datos['registros'][2]
        self.assertEqual([libro['Catálogo'].cell(4, c).value for c in range(2, 8)],
                         [r['clave'], r['clave'], r['descripcion'], r['descripcion'], r['unidad'], 12.5])
        self.assertEqual(libro['Copiar auxiliares']['B4'].value, r['clave'])
        self.assertEqual(libro['Revisión']['N6'].value, 'Revisor de prueba')
        self.assertIsNone(libro['Revisión']['P6'].value)  # No se inventa verificación SQL sin matriz.
        self.assertIn('Sin matriz por decisión del usuario (1)', revision.reporte(datos, final=True))
        self.assertIn('Motivo del usuario', revision.reporte(datos, final=True))

    def test_sin_candidatos_se_conserva_y_fallo_busqueda_no_se_confunde(self):
        b = self.datos['busquedas_construbase'][0]
        b.update(candidatos=[], estado='sin_candidatos_en_busqueda')
        libro = exportar.crear_excel(self.datos, final=True)
        self.assertEqual(libro['Catálogo']['B4'].value, '001.00')
        libro.close()
        self.assertIn('Sin candidatos encontrados (1)', revision.reporte(self.datos, final=True))
        for estado in ('requiere_terminos', 'error_evaluacion_ia'):
            b['estado'] = estado
            with self.assertRaises(ValueError): exportar.crear_excel(self.datos, final=True)

    def test_codigo_faltante_solicitado_sin_alterar_ir(self):
        self.datos['registros'][2]['clave'] = None
        with self.assertRaisesRegex(ValueError, 'código'): self.manual()
        datos = self.manual(codigo='NUEVO-USUARIO')
        self.assertIsNone(datos['registros'][2]['clave'])
        libro = exportar.crear_excel(datos, final=True)
        self.assertEqual(libro['Catálogo']['B4'].value, 'NUEVO-USUARIO')
        self.assertEqual(libro['Catálogo']['C4'].value, 'NUEVO-USUARIO')
        libro.close()
        with self.assertRaises(ValueError): self.manual(codigo='')

    def test_no_se_reemplazan_codigos_decisiones_ni_huellas(self):
        with self.assertRaises(ValueError): self.manual(codigo='CAMBIADO')
        datos = self.manual()
        with self.assertRaises(ValueError): confirmar.confirmar(datos, [dict(self.ejemplo.decisiones()[0], IdCodigo=None)], None)
        datos['registros'][2]['descripcion'] = 'Modificado'
        with self.assertRaises(ValueError): exportar.crear_excel(datos, final=True)

    def test_tres_opciones_descripciones_completas_y_cuarta_sin_matriz(self):
        b = self.datos['busquedas_construbase'][0]
        c = b['candidatos'][0]
        b['candidatos'] = [dict(c, IdCodigo=i, Codigo=f'CB-{i}') for i in range(1, 6)]
        b['evaluacion_ia'] = dict(motivo='Pendiente', candidatos=[dict(IdCodigo=1, dictamen='incompatible', motivo='Material distinto')])
        self.assertEqual([c['IdCodigo'] for c, _ in revision.opciones(b)], [2, 3, 4])
        md = revision.reporte(self.datos)
        self.assertIn('4. Conservar concepto original', md)
        self.assertIn('Descripción íntegra ConstruBase', md)
        self.assertNotIn('IdCodigo 5', md)
        with self.assertRaisesRegex(ValueError, 'decisión'): exportar.crear_excel(self.datos, final=True)

    def test_matriz_humana_sigue_verificada_y_reporte_distingue_origen(self):
        datos = confirmar.confirmar(self.datos, self.ejemplo.decisiones(), self.ejemplo.conexion())
        libro = exportar.crear_excel(datos, final=True)
        self.assertEqual(libro['Catálogo']['B4'].value, 'CB-001')
        self.assertEqual(libro['Catálogo']['D4'].value, self.datos['busquedas_construbase'][0]['candidatos'][0]['DescripcionLarga'])
        libro.close()
        self.assertIn('Con matriz seleccionada (1)', revision.reporte(datos, final=True))
        self.assertIn('Origen: Usuario', revision.reporte(datos, final=True))

    def test_cli_excel_y_md_juntos_y_no_sobrescribe_reporte(self):
        with tempfile.TemporaryDirectory() as carpeta:
            entrada, destino = Path(carpeta)/'entrada.json', Path(carpeta)/'final.xlsx'
            entrada.write_text(json.dumps(self.manual()), encoding='utf-8')
            with patch('sys.argv', ['exportar', str(entrada), '--final', '--salida', str(destino)]): exportar.main()
            self.assertTrue(destino.with_suffix('.md').exists())
            libro = load_workbook(destino)
            self.assertEqual(libro['Catálogo']['B4'].value, '001.00')
            self.assertEqual(tuple(c.value for c in libro['Catálogo'][1]), exportar.COLUMNAS)
            libro.close()
            otro = Path(carpeta)/'otro.xlsx'
            otro.with_suffix('.md').write_text('No tocar', encoding='utf-8')
            with patch('sys.argv', ['exportar', str(entrada), '--final', '--salida', str(otro)]), self.assertRaises(SystemExit): exportar.main()
            self.assertFalse(otro.exists())
            self.assertEqual(otro.with_suffix('.md').read_text(encoding='utf-8'), 'No tocar')

    def test_selector_no_evalua_ausencia_y_no_reemplaza_decision_humana(self):
        b = self.datos['busquedas_construbase'][0]
        b.update(candidatos=[], estado='sin_candidatos_en_busqueda')
        with patch.object(selector, 'configuracion', return_value=('local', 'modelo', '')), patch.object(selector, 'comparar') as comparar:
            datos = selector.seleccionar(self.datos, None)
            comparar.assert_not_called()
            self.assertEqual(datos['resumen_ia']['errores'], 0)
            self.assertEqual(datos['resumen_ia']['sin_candidatos'], 1)
            self.assertEqual(datos['resumen_ia']['pendientes'], 0)
            self.assertIn('Sin candidatos encontrados (1)', revision.reporte(datos, final=True))
            with self.assertRaises(ValueError): selector.seleccionar(self.manual(), None)

    def test_presupuesto_mixto_con_tres_categorias_y_una_sola_consulta_sql(self):
        r = self.datos['registros'][2]
        self.datos['registros'] += [dict(r, fila=4, clave='CLIENTE-2'), dict(r, fila=5, clave='CLIENTE-3')]
        b = self.datos['busquedas_construbase'][0]
        self.datos['busquedas_construbase'] += [dict(deepcopy(b), fila=4),
            dict(hoja='Obra', fila=5, candidatos=[], seleccion=None, estado='sin_candidatos_en_busqueda')]
        decisiones = self.ejemplo.decisiones() + [dict(self.ejemplo.decisiones()[0], fila=4, IdCodigo=None)]
        conexion = self.ejemplo.conexion()
        datos = confirmar.confirmar(self.datos, decisiones, conexion)
        self.assertEqual(conexion.cursor.return_value.execute.call_count, 1)
        libro = exportar.crear_excel(datos, final=True)
        self.assertEqual([libro['Catálogo'].cell(n, 2).value for n in (4, 5, 6)], ['CB-001', 'CLIENTE-2', 'CLIENTE-3'])
        self.assertEqual([libro['Catálogo'].cell(n, 1).value for n in (4, 5, 6)], ['A.A01'] * 3)
        libro.close()
        md = revision.reporte(datos, final=True)
        for categoria in ('Sin candidatos encontrados', 'Sin matriz por decisión del usuario', 'Con matriz seleccionada'):
            self.assertIn(categoria + ' (1)', md)

    def test_cli_sin_matriz_no_requiere_sql_y_codigo_faltante_no_crea_excel(self):
        with tempfile.TemporaryDirectory() as carpeta:
            entrada, decisiones, salida = [Path(carpeta)/n for n in ('entrada.json', 'decisiones.json', 'salida.json')]
            entrada.write_text(json.dumps(self.datos), encoding='utf-8')
            decisiones.write_text(json.dumps([dict(self.ejemplo.decisiones()[0], IdCodigo=None)]), encoding='utf-8')
            with patch('sys.argv', ['confirmar', str(entrada), str(decisiones), '--salida', str(salida)]), patch.object(confirmar, 'conectar_sql') as sql:
                confirmar.main()
                sql.assert_not_called()
            self.datos['registros'][2]['clave'] = None
            self.datos['busquedas_construbase'][0].update(candidatos=[], estado='sin_candidatos_en_busqueda')
            entrada.write_text(json.dumps(self.datos), encoding='utf-8')
            destino = Path(carpeta)/'incompleto.xlsx'
            with patch('sys.argv', ['exportar', str(entrada), '--final', '--salida', str(destino)]), self.assertRaisesRegex(ValueError, 'código'):
                exportar.main()
            self.assertFalse(destino.exists())
            self.assertFalse(destino.with_suffix('.md').exists())
