"""Repositorio CRUD genérico sobre un archivo JSON.
Cada modelo (Metrica, Tarea, Entidad) hereda de esto y define su propio
tipo de dato; este archivo no sabe nada de negocio, solo persiste listas
de diccionarios con un campo 'id' autoincremental.
"""
import json
import threading
from pathlib import Path
from typing import Any, Callable


class JsonRepository:
    _lock = threading.Lock()

    def __init__(self, ruta_archivo: Path, factory: Callable[[dict], Any],
                 to_dict: Callable[[Any], dict]):
        """
        ruta_archivo: Path al .json (se crea vacío si no existe).
        factory: función dict -> objeto de dominio (ej. dict -> Metrica).
        to_dict: función objeto de dominio -> dict (para guardar).
        """
        self.ruta = Path(ruta_archivo)
        self._factory = factory
        self._to_dict = to_dict
        if not self.ruta.exists():
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            self.ruta.write_text("[]", encoding="utf-8")

    def _leer_crudo(self) -> list[dict]:
        with open(self.ruta, "r", encoding="utf-8") as f:
            return json.load(f)

    def _escribir_crudo(self, datos: list[dict]) -> None:
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    def listar(self) -> list:
        return [self._factory(d) for d in self._leer_crudo()]

    def obtener(self, id_: int):
        for d in self._leer_crudo():
            if d.get("id") == id_:
                return self._factory(d)
        return None

    def crear(self, objeto) -> Any:
        with self._lock:
            datos = self._leer_crudo()
            siguiente_id = (max((d.get("id", 0) for d in datos), default=0)) + 1
            dict_obj = self._to_dict(objeto)
            dict_obj["id"] = siguiente_id
            datos.append(dict_obj)
            self._escribir_crudo(datos)
            return self._factory(dict_obj)

    def actualizar(self, id_: int, objeto) -> Any | None:
        with self._lock:
            datos = self._leer_crudo()
            for i, d in enumerate(datos):
                if d.get("id") == id_:
                    dict_obj = self._to_dict(objeto)
                    dict_obj["id"] = id_
                    datos[i] = dict_obj
                    self._escribir_crudo(datos)
                    return self._factory(dict_obj)
            return None

    def eliminar(self, id_: int) -> bool:
        with self._lock:
            datos = self._leer_crudo()
            filtrados = [d for d in datos if d.get("id") != id_]
            if len(filtrados) == len(datos):
                return False
            self._escribir_crudo(filtrados)
            return True