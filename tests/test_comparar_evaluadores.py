from copy import deepcopy
import json
import unittest
from unittest.mock import patch

try:
    import comparar_evaluadores as experimento
except ModuleNotFoundError as exc:
    if exc.name != "numpy":
        raise
    experimento = None


@unittest.skipIf(experimento is None, "Laboratorio opcional sin numpy instalado")
class PruebasComparacionEvaluadores(unittest.TestCase):
    def muestra(self):
        return dict(registros=[dict(tipo="concepto",hoja="Obra",fila=3,descripcion="Cliente original",
                unidad="M2 ",cantidad="001.00")],busquedas_construbase=[dict(hoja="Obra",fila=3,
                candidatos=[dict(IdCodigo=7,Codigo="CB-007",DescripcionLarga="Catálogo íntegro",unidad_catalogo="M2")])])

    def test_mismos_pares_y_textos_exactos_sin_mutar_la_muestra(self):
        datos=self.muestra();antes=deepcopy(datos)
        pares=experimento.pares(datos,deepcopy(datos))
        self.assertEqual(datos,antes)
        self.assertEqual(pares[0]["estado"]["cliente"]["cantidad"],"001.00")
        self.assertEqual(pares[0]["estado"]["catalogo"]["descripcion"],"Catálogo íntegro")
        self.assertEqual(pares[0]["estado_sha256"],experimento.huella(pares[0]["estado"]))

    def test_cambio_de_conceptos_o_candidatos_no_es_comparacion_controlada(self):
        datos=self.muestra()
        for caso in ("concepto","candidato","duplicado"):
            otra=deepcopy(datos)
            if caso=="concepto": otra["registros"][0]["descripcion"]="Otro"
            elif caso=="candidato": otra["busquedas_construbase"][0]["candidatos"][0]["DescripcionLarga"]="Otro"
            else: otra["busquedas_construbase"]*=2
            with self.subTest(caso=caso),self.assertRaises(ValueError):
                experimento.pares(otra,datos)

    def test_confianza_alta_no_se_convierte_en_aprobacion(self):
        probabilidades=dict.fromkeys(experimento.CRITERIOS,0.0);probabilidades["incompatible"]=1.0
        respuesta=dict(answers=dict(compatibilidad=dict(choice="incompatible",probabilities=probabilidades,confidence=1.0)))
        with patch.object(experimento,"post",return_value=respuesta):
            resultado=experimento.evaluar_decision("local","tev1",{})
        self.assertEqual(resultado["decision"],"incompatible")
        self.assertNotIn("seleccion",resultado)
        self.assertNotIn("aprobado",resultado)

    def test_categoria_o_probabilidades_invalidas_no_generan_resultados(self):
        for decision,probabilidades in (("inventada",None),("equivalente",{}),
                ("equivalente",dict.fromkeys(experimento.CRITERIOS,float("nan")))):
            with self.subTest(decision=decision),self.assertRaises(ValueError):
                experimento.validar_decision(decision,probabilidades)

    def test_nemotron_recibe_el_mismo_estado_y_cuatro_categorias(self):
        estado=experimento.pares(self.muestra(),self.muestra())[0]["estado"]
        with patch.object(experimento,"consultar_ia",return_value=json.dumps(dict(
                decision="compatible_con_diferencias",motivo="Diferencias de alcance pendientes"))) as consultar:
            resultado=experimento.evaluar_nemotron(estado)
        contenido=json.loads(consultar.call_args.args[0][1]["content"])
        self.assertEqual(contenido["state"],estado)
        self.assertEqual(contenido["questions"]["compatibilidad"]["criteria"],experimento.CRITERIOS)
        self.assertEqual(resultado["decision"],"compatible_con_diferencias")

    def test_control_de_orden_conserva_exactamente_el_estado_y_la_rubrica(self):
        probs=dict.fromkeys(experimento.CRITERIOS,0.25)
        respuesta=dict(answers=dict(compatibilidad=dict(choice="insuficiente",probabilities=probs)))
        estado={"cliente":"original","catalogo":"original"}
        orden=list(reversed(experimento.CRITERIOS))
        with patch.object(experimento,"post",return_value=respuesta) as post:
            experimento.evaluar_decision("local","d1",estado,orden=orden)
        cuerpo=post.call_args.args[2]
        self.assertEqual(cuerpo["state"],estado)
        self.assertEqual(cuerpo["questions"]["compatibilidad"]["criteria"],experimento.CRITERIOS)
        self.assertEqual(list(cuerpo["questions"]["compatibilidad"]["criteria"]),orden)
