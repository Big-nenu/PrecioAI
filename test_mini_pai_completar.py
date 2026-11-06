from copy import deepcopy
import unittest
from mini_pai_completar import completar

class PruebasCompletar(unittest.TestCase):
    def setUp(self):
        self.datos = dict(dudas=[], registros=[dict(tipo='concepto', hoja='Obra', fila=2,
            clave='X', descripcion='Trabajo', unidad=None, cantidad='0', partida=None,
            subpartida=None, padre=None, evidencia=dict(clave=['A2'], descripcion=['F2'], unidad=[], cantidad=['J2']))])
        self.inspeccion = dict(hojas=[dict(nombre='Obra', filas=[dict(fila=2, celdas={'A2':'X','F2':'Trabajo','J2':'0','Z2':'m²'}), dict(fila=3,celdas={'Z3':'otra'})])])
        self.cambio = dict(hoja='Obra',fila=2,campo='unidad',celdas=['Z2'])

    def test_completa_exactamente_sin_columnas_fijas_y_preserva_origen(self):
        antes = deepcopy(self.datos)
        salida = completar(self.datos,self.inspeccion,[self.cambio],'hash')
        self.assertEqual(self.datos,antes)
        self.assertEqual(salida['registros'][0]['unidad'],'m²')
        self.assertEqual(salida['registros'][0]['cantidad'],'0')
        self.assertEqual(salida['completados'][0]['excel_sha256'],'hash')

    def test_rechaza_celda_vacia_ajena_duplicada_y_sobrescritura(self):
        for refs in (['Z99'],['Z3'],['Z2','Z2']):
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                completar(self.datos,self.inspeccion,[dict(self.cambio,celdas=refs)],'hash')
        with self.assertRaises(ValueError):
            completar(self.datos,self.inspeccion,[dict(self.cambio,campo='cantidad')],'hash')
        with self.assertRaises(ValueError):
            completar(self.datos,self.inspeccion,[self.cambio,self.cambio],'hash')

    def test_rechaza_busquedas_obsoletas_y_excel_distinto(self):
        with self.assertRaises(ValueError):
            completar(dict(self.datos,busquedas_construbase=[]),self.inspeccion,[self.cambio],'hash')
        inspeccion=deepcopy(self.inspeccion)
        inspeccion['hojas'][0]['filas'][0]['celdas']['F2']='Otro trabajo'
        with self.assertRaises(ValueError):
            completar(self.datos,inspeccion,[self.cambio],'hash')
