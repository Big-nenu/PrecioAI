from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from mini_pai_tabla import clasificar_tabla,materializar_tabla
from mini_pai_buscar import validar_entrada,buscar_presupuesto
from mini_pai_interpretar import descripcion_tecnica
from mini_pai_seleccionar import fragmentos
from mini_pai_claves import interpretar_claves
from mini_pai_exportar import crear_excel,COLUMNAS
from tests import test_mini_pai_buscar as ejemplos


class ContextosCompartidos(unittest.TestCase):
    def fuente(self):
        filas=[dict(fila=1,celdas={'C1':'Clave','E1':'Descripción','H1':'Unidad','M1':'Cantidad'})]
        for n,key,desc in [(2,'Z','Sección'),(3,'K','Suministro de panel de madera. Incluye colocación.'),
                           (4,'X','De 0.70 x 0.60 m'),(5,'Y','De 0.90 x 0.80 m'),
                           (6,'N','Otros trabajos'),(7,'W','Otra actividad independiente')]:
            filas.append(dict(fila=n,celdas={f'C{n}':key,f'E{n}':desc,**({f'H{n}':'PZA',f'M{n}':'2'} if n in (4,5,7) else {})}))
        fuente=dict(hojas=[dict(nombre='Hoja',filas=filas)])
        e=dict(hoja='Hoja',encabezado=1,columnas=dict(clave='C1',descripcion='E1',unidad='H1',cantidad='M1'))
        plan=dict(resumen_desde=None,dudas=[],filas={'2':dict(tipo='partida',padre=None,motivo=None),
            '3':dict(tipo='subpartida',padre=2,motivo=None),'6':dict(tipo='subpartida',padre=2,motivo=None)},
            contextos={'3':dict(hijo=4,motivo='La actividad general se completa con dimensiones del hijo')})
        return fuente,e,plan

    def datos(self):
        f,e,p=self.fuente();return materializar_tabla(f,e,p)

    def test_origen_contexto_y_auxiliares_sin_reescritura(self):
        f,e,p=self.fuente();antes=deepcopy((f,e,p));d=materializar_tabla(f,e,p);validar_entrada(d,{})
        self.assertEqual((f,e,p),antes)
        por_fila={r['fila']:r for r in d['registros']}
        for n in (4,5):
            self.assertEqual(por_fila[n]['contexto_descripcion'][0]['fila'],3)
            self.assertEqual(por_fila[n]['contexto_descripcion'][0]['evidencia'],['E3'])
        self.assertNotIn('contexto_descripcion',por_fila[7])
        libro=crear_excel(d)
        self.assertEqual(tuple(c.value for c in libro['Catálogo'][1]),COLUMNAS)
        self.assertEqual(libro['Catálogo']['E4'].value,'De 0.70 x 0.60 m')
        self.assertEqual(libro['Catálogo']['C4'].value,'X')
        self.assertEqual(libro['Catálogo']['D3'].value,por_fila[3]['descripcion'])
        libro.close()

    def test_rechaza_contexto_cambiado_omitido_o_de_otro_grupo(self):
        d=self.datos()
        for cambio in ('texto','omitir','hijo'):
            x=deepcopy(d)
            if cambio=='texto':x['registros'][2]['contexto_descripcion'][0]['descripcion']='Concreto inventado'
            elif cambio=='omitir':del x['registros'][2]['contexto_descripcion']
            else:x['registros'][1]['descripcion_compartida']['hijo']=7
            with self.subTest(cambio=cambio),self.assertRaises(ValueError):validar_entrada(x,{})

    def test_revision_declara_relacion_con_hijo_real_sin_inventar_campos(self):
        f,e,p=self.fuente()
        d=materializar_tabla(f,e,p)
        self.assertIn('panel de madera',descripcion_tecnica(d['registros'][2]))
        p['contextos']['3']['hijo']=7
        with self.assertRaises(ValueError):materializar_tabla(f,e,p)

    def test_recuperacion_y_fragmentos_utilizan_contexto_conservando_cliente(self):
        d=self.datos();antes=deepcopy(d);helper=ejemplos.PruebasBusquedaPresupuesto()
        with patch('mini_pai_buscar.buscar',return_value=[]) as sql:
            buscar_presupuesto(d,helper.conexion())
        self.assertIn('panel',sql.call_args_list[0].args[1])
        r=d['registros'][2];fuentes=fragmentos(r,dict(candidatos=[]))
        self.assertEqual(fuentes['C0'],r['descripcion'])
        self.assertIn('Suministro de panel',fuentes['CC0_0'])
        self.assertEqual(d,antes)

    def test_atributos_del_contexto_con_citas_sin_reescribir_cliente(self):
        r=self.datos()['registros'][2]
        wire=dict(actividad=dict(nombre='Suministro de panel',evidencia='CC0_0'),
            atributos=[dict(nombre='material',valor='madera',evidencia='CC0_0')],
            consultas=['panel madera','panel'],dudas=[])
        with patch('mini_pai_claves.consultar_ia',return_value=json.dumps(wire)):
            plan=interpretar_claves(r,'')
        self.assertEqual(plan['atributos'][0]['valor'],'madera')
        self.assertEqual(r['descripcion'],'De 0.70 x 0.60 m')

    def test_revision_por_hash_sin_llamar_modelo_y_rechazo_de_origen_distinto(self):
        import tempfile,hashlib
        from pathlib import Path
        from openpyxl import Workbook
        from mini_pai_tabla import interpretar_tabla
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta);entrada=raiz/'entrada.xlsx';revision=raiz/'revision.json'
            f,e,plan=self.fuente();w=Workbook();w.active.title='Hoja'
            for r in f['hojas'][0]['filas']:
                for coord,valor in r['celdas'].items():w.active[coord]=valor
            w.save(entrada);w.close();original=entrada.read_bytes()
            datos=dict(version=1,archivo_sha256=hashlib.sha256(original).hexdigest(),estructura=e,plan=plan,
                revisor='Agente de prueba',motivo='Decisiones explícitas cotejadas con el original')
            revision.write_text(json.dumps(datos),encoding='utf-8')
            with patch('mini_pai_tabla.consultar_ia',side_effect=AssertionError('No debe llamar IA')):
                resultado=interpretar_tabla(entrada,revision=revision)
            self.assertEqual(resultado['revision_estructura']['revisor'],'Agente de prueba')
            self.assertEqual(resultado['registros'][2]['contexto_descripcion'][0]['fila'],3)
            self.assertEqual(original,entrada.read_bytes())
            for cambio in ('hash','version','revisor','fila'):
                copia=deepcopy(datos)
                if cambio=='hash':copia['archivo_sha256']='otro'
                elif cambio=='version':copia['version']=True
                elif cambio=='revisor':copia['revisor']=' '
                else:copia['plan']['filas']['999']=dict(tipo='partida',padre=None,motivo=None)
                revision.write_text(json.dumps(copia),encoding='utf-8')
                with self.subTest(cambio=cambio),self.assertRaises(ValueError):
                    interpretar_tabla(entrada,revision=revision)

    def test_evidencia_tecnica_del_contexto_sin_rebajar_controles(self):
        from mini_pai_confirmar import validar_evaluacion_ia
        r=self.datos()['registros'][2]
        b=dict(candidatos=[dict(IdCodigo=1,Codigo='CB',DescripcionLarga='Suministro de panel de madera',IdTipo=4,IdUnidad=1,unidad_catalogo='PZA')])
        evaluacion=dict(seleccion_id=None,motivo='Pendiente de verificar dimensiones y alcance',comprobaciones=[],
            candidatos=[dict(IdCodigo=1,dictamen='insuficiente',motivo='La actividad es la misma, faltan detalles',cliente='panel de madera',catalogo='panel de madera')])
        validar_evaluacion_ia(r,b,evaluacion)
        evaluacion['candidatos'][0]['cliente']='Concreto armado'
        with self.assertRaises(ValueError):validar_evaluacion_ia(r,b,evaluacion)

    def test_resistencia_y_espesor_del_contexto_no_se_ignoran(self):
        from tests import test_mini_pai_seleccionar as controles
        from mini_pai_confirmar import validar_evaluacion_ia
        ayuda=controles.PruebasSeleccionIA();datos=ayuda.datos();r=datos['registros'][2];b=datos['busquedas_construbase'][0]
        r['contexto_descripcion']=[dict(hoja='Obra',fila=2,descripcion='Espesor 6 cm',evidencia=['D2'])]
        b['candidatos'][0]['DescripcionLarga']+=' Espesor 6 cm'
        e=ayuda.evaluacion()
        for c in e['comprobaciones']:
            if c['aspecto'] in ('espesor','dimensiones'):
                c.update(estado='compatible',cliente='Espesor 6 cm',catalogo='Espesor 6 cm')
        validar_evaluacion_ia(r,b,e)
        b['candidatos'][0]['DescripcionLarga']+=' Espesor 5 cm'
        next(c for c in e['comprobaciones'] if c['aspecto']=='espesor')['catalogo']='Espesor 5 cm'
        with self.assertRaisesRegex(ValueError,'Valores técnicos distintos'):
            validar_evaluacion_ia(r,b,e)

    def test_reporte_explica_contexto_sin_cambiar_las_descripciones(self):
        from mini_pai_revision import reporte
        d=self.datos();antes=deepcopy(d);texto=reporte(d)
        self.assertIn('Contexto común (Hoja:3)',texto)
        self.assertIn('Suministro de panel de madera',texto)
        self.assertEqual(d,antes)

    def test_cli_no_sobrescribe_revision_ni_la_ignora_sin_por_tabla(self):
        import tempfile,io
        from pathlib import Path
        from mini_pai_interpretar import main
        with tempfile.TemporaryDirectory() as carpeta:
            entrada=Path(carpeta)/'original.xlsx';entrada.write_bytes(b'Original protegido')
            revision=Path(carpeta)/'revision.json';revision.write_text('{}',encoding='utf-8')
            base=['interpretar',str(entrada),'--revision-estructura',str(revision)]
            for extra in ([],['--por-tabla','--salida',str(revision)]):
                with patch('sys.argv',base+extra),patch('sys.stderr',new_callable=io.StringIO),self.assertRaises(SystemExit):
                    main()
                self.assertEqual(revision.read_text(encoding='utf-8'),'{}')
                self.assertEqual(entrada.read_bytes(),b'Original protegido')
