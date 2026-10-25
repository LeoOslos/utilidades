#!/usr/bin/env python3
"""Tests de registro_log.py. Correr: python3 -m unittest discover -s tests
"""

import contextlib
import io
import logging
import os
import tempfile
import unittest

import registro_log

LINEA = r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d -03 [A-Z]+ \S+ \S+ "


class RegistroLog(unittest.TestCase):
    def tearDown(self):
        raiz = logging.getLogger()
        for h in [h for h in raiz.handlers if getattr(h, "_registro_log", False)]:
            raiz.removeHandler(h)
            h.close()

    def capturar(self, fn, **kw):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            log = registro_log.configurar_logging("prueba", **kw)
            fn(log)
        return salida.getvalue().splitlines()

    def test_al_apagarse_el_interprete_la_fecha_no_rompe(self):
        """zoneinfo no puede importar durante el apagado: la fecha sale igual, en -03 fijo."""
        class Roto:
            @staticmethod
            def fromtimestamp(*a, **k):
                raise ImportError("sys.meta_path is None, Python is likely shutting down")
        f = registro_log.FormatoEstandar("prueba")
        rec = logging.LogRecord("x", logging.ERROR, __file__, 1, "msg", None, None)
        rec.created = 1791674465.0  # 2026-10-10 20:21:05 -03
        normal = f.formatTime(rec)
        original, registro_log.datetime = registro_log.datetime, Roto
        try:
            self.assertEqual(f.formatTime(rec), normal)
        finally:
            registro_log.datetime = original
        self.assertEqual(normal, "2026-10-10 20:21:05 -03")

    def test_formato(self):
        lineas = self.capturar(lambda log: (log.info("hola"), log.warning("ojo")))
        self.assertEqual(len(lineas), 2)
        for l in lineas:
            self.assertRegex(l, LINEA)
        self.assertRegex(lineas[0], r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d -03 INFO prueba \S+ hola$")
        self.assertIn(" WARNING prueba ", lineas[1])

    def test_traceback_con_prefijo_en_cada_linea(self):
        def fallar(log):
            try:
                1 / 0
            except ZeroDivisionError:
                log.exception("falló")
        lineas = self.capturar(fallar)
        self.assertGreater(len(lineas), 3)
        for l in lineas:
            self.assertRegex(l, r"^\S+ \S+ -03 ERROR prueba \S+ ")
        self.assertTrue(lineas[-1].endswith("ZeroDivisionError: division by zero"))

    def test_no_duplica_si_se_configura_dos_veces(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            registro_log.configurar_logging("prueba")
            registro_log.configurar_logging("prueba").info("una vez")
        self.assertEqual(salida.getvalue().count("una vez"), 1)

    def test_archivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "sub", "prueba.log")
            self.capturar(lambda log: log.info("al archivo"), archivo=ruta)
            with open(ruta, encoding="utf-8") as f:
                self.assertIn(" INFO prueba ", f.read())

    def test_proceso_invalido(self):
        with self.assertRaises(ValueError):
            registro_log.configurar_logging("con espacio")


class LoggerAArchivo(unittest.TestCase):
    def test_escribe_solo_en_su_archivo_con_formato(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "sub", "modulo.log")
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(salida):
                registro_log.configurar_logging("principal")
                log = registro_log.logger_a_archivo("modulo", ruta)
                log.warning("FALLO algo\n    cd ~/x && reintentar")
                self.assertIs(log, registro_log.logger_a_archivo("modulo", ruta))
            for h in log.handlers:
                h.close()
            with open(ruta, encoding="utf-8") as f:
                lineas = f.read().splitlines()
            self.assertEqual(salida.getvalue(), "")
            self.assertEqual(len(lineas), 2)
            for l in lineas:
                self.assertRegex(l, r"^\S+ \S+ -03 WARNING modulo \S+ ")
        raiz = logging.getLogger()
        for h in [h for h in raiz.handlers if getattr(h, "_registro_log", False)]:
            raiz.removeHandler(h)
            h.close()

    def test_no_crea_archivo_hasta_escribir(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "vacio.log")
            registro_log.logger_a_archivo("vacio", ruta)
            self.assertFalse(os.path.exists(ruta))


if __name__ == "__main__":
    unittest.main()
