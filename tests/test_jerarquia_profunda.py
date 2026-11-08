import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from mini_pai_interpretar import materializar, validar
from mini_pai_buscar import validar_entrada
from mini_pai_exportar import crear_excel, COLUMNAS
from mini_pai_tabla import clasificar_tabla


class JerarquiaProfunda(unittest.TestCase):
    def ejemplo(self):
        # Claves sin prefijos comunes; la relación viene del plan, no del texto.
        hojas=dict(hojas=[dict(nombre='Obra',filas=[
            dict(fila=1,celdas={'A1':'Clave','B1':'Descripción','C1':'Unidad','D1':'Cantidad'}),
            *[dict(fila=n,celdas={f'A{n}':clave,f'B{n}':descripcion,
                **({f'C{n}':'M2',f'D{n}':'12.50'} if n in (6,8) else {})})
              for n,clave,descripcion in [(2,'Z','Zona'),(3,'K','Sección'),(4,'R','Rama'),
                (5,'T','Subrama'),(6,'X','Trabajo original'),(7,'N','Otra sección'),(8,'Y','Otro trabajo')]]])])
        tipos={1:'omitir',2:'partida',3:'subpartida',4:'subpartida',5:'subpartida',6:'concepto',7:'subpartida',8:'concepto'}
        padres={1:None,2:None,3:2,4:3,5:4,6:5,7:2,8:7}
        propuesta=dict(dudas=[],registros=[dict(hoja='Obra',fila=n,tipo=tipos[n],padre=padres[n],
            motivo='Cabecera' if n==1 else None,evidencia={c:([col+str(n)] if n!=1 and (c in ('clave','descripcion') or n in (6,8)) else [])
                for c,col in [('clave','A'),('descripcion','B'),('unidad','C'),('cantidad','D')]}) for n in range(1,9)])
        return hojas,propuesta

    def test_arbol_completo_valida_y_exporta_con_las_mismas_columnas(self):
        origen,plan=self.ejemplo();datos=materializar(plan,origen)
        validar(datos,origen);validar_entrada(datos,{})
        self.assertEqual([r['padre'] for r in datos['registros']],[None,2,3,4,5,2,7])
        datos['busquedas_construbase']=[dict(hoja='Obra',fila=n,candidatos=[],estado='sin_candidatos_en_busqueda') for n in (6,8)]
        libro=crear_excel(datos,final=True)
        self.assertEqual(tuple(c.value for c in libro['Catálogo'][1]),COLUMNAS)
        self.assertEqual(libro['Catálogo']['A6'].value,'Z.K.R.T')
        self.assertEqual(libro['Catálogo']['B6'].value,'X')
        self.assertEqual(libro['Catálogo']['D6'].value,'Trabajo original')
        self.assertEqual(libro['Catálogo']['A8'].value,'Z.N')
        libro.close()

    def test_rutas_con_prefijos_relativos_no_duplican_niveles(self):
        origen,plan=self.ejemplo()
        origen['hojas'][0]['filas'][3]['celdas']['A4']='K.R'
        origen['hojas'][0]['filas'][4]['celdas']['A5']='K.R.T'
        datos=materializar(plan,origen)
        libro=crear_excel(datos)
        self.assertEqual(libro['Catálogo']['A6'].value,'Z.K.R.T')
        libro.close()

    def test_rechaza_ramas_cerradas_y_padres_que_saltan_grupo_vigente(self):
        origen,plan=self.ejemplo()
        for fila,padre in ((8,5),(6,2),(4,8)):
            copia=deepcopy(plan);copia['registros'][fila-1]['padre']=padre
            with self.subTest(fila=fila),self.assertRaises(ValueError):
                validar(materializar(copia,origen),origen)

    def test_duda_estructural_no_se_reintenta_para_forzar_aceptacion(self):
        from mini_pai_tabla import RevisionEstructural
        origen,_=self.ejemplo()
        estructura=dict(hoja='Obra',encabezado=1,columnas=dict(clave='A1',descripcion='B1',unidad='C1',cantidad='D1'))
        wire=dict(dudas=[],filas={str(n):dict(tipo='revision',padre=None,motivo='No hay datos suficientes para distinguir grupo y trabajo') for n in (2,3,4,5,7)})
        with patch('mini_pai_tabla.consultar_ia',return_value=json.dumps(wire)) as ia,self.assertRaises(RevisionEstructural):
            clasificar_tabla(origen,estructura)
        self.assertEqual(ia.call_count,1)
        roles=ia.call_args.kwargs['esquema']['properties']['filas']['properties']['2']['properties']['tipo']['enum']
        self.assertNotIn('concepto',roles)
        self.assertIn('revision',roles)

    def test_clasificador_conserva_niveles_sin_letras_fijas(self):
        origen,_=self.ejemplo()
        estructura=dict(hoja='Obra',encabezado=1,columnas=dict(clave='A1',descripcion='B1',unidad='C1',cantidad='D1'))
        padres={2:None,3:2,4:3,5:4,7:2}
        wire=dict(dudas=[],filas={str(n):dict(tipo='partida' if padre is None else 'subpartida',padre=padre,motivo=None) for n,padre in padres.items()})
        with patch('mini_pai_tabla.consultar_ia',return_value=json.dumps(wire)):
            datos=clasificar_tabla(origen,estructura)
        self.assertEqual([r['padre'] for r in datos['registros']],[None,2,3,4,5,2,7])
        wire['filas']['3']['padre']=8
        with patch('mini_pai_tabla.consultar_ia',return_value=json.dumps(wire)),self.assertRaisesRegex(ValueError,'padre inexistente'):
            clasificar_tabla(origen,estructura)
