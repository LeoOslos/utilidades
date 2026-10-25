# utilidades

Código común a varios proyectos propios, instalable por pip en el venv de cada uno. Hoy trae un solo
módulo: `registro_log`, un formato estándar de log.

## Cómo funciona, explicado

Antes, cada proyecto tenía su propia copia de `registro_log.py`: un arreglo había que copiarlo a
mano a cada lugar y se quedaba en uno solo. Ahora el módulo vive acá, una vez, y cada proyecto
declara en su `requirements.txt` qué versión usa:

```
utilidades @ git+ssh://git@github.com/LeoOslos/utilidades.git@v1.0.0
```

`pip install -r requirements.txt` clona el repo en ese tag y deja `registro_log` instalado en el
venv. El código del proyecto no cambia: sigue haciendo `from registro_log import configurar_logging`.
Un arreglo se publica con un tag nuevo, y cada proyecto sube de versión cuando quiere, cambiando esa
línea; un servicio que ya está corriendo lo toma en su próximo reinicio.

## Publicar una versión

1. Cambiar el módulo y sus tests; `venv/bin/python -m unittest discover -s tests`.
2. Subir `version` en `pyproject.toml` (SemVer: MAJOR rompe la interfaz, MINOR agrega, PATCH corrige).
3. Commit, `git tag vX.Y.Z -m "…"`, `git push origin master vX.Y.Z`.
4. En cada proyecto que lo quiera: cambiar el tag en `requirements.txt` y reinstalar.

## Desarrollo

```
python3 -m venv venv && venv/bin/pip install -e .
venv/bin/python -m unittest discover -s tests
```
