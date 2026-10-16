# Primer acondicionamiento — Dimmery

**Proyecto:** dimmery
**Descripcion:** Brightness that learns your habits for a DDC/CI external monitor
**Autor:** circularnatural
**Origen:** project-template (generado con Copier, via el wrapper `scripts/init-from-template.py`)

Esto es un scaffold, no un producto terminado. Copier ya resolvio la parte
mecanica: renombrar `project_name` en todos los archivos, sustituir variables,
gatear archivos segun los flags `include_*`, resetear `CHANGELOG.md`/`VERSION`/
`CONTRIBUTORS.md`/`governance/*` a esqueleto, y generar este documento. Tu
trabajo ahora es la parte que necesita criterio humano/agente.


## Lo que tenes que hacer, en orden

1. **`AGENTS.md`** — completa la seccion "What this project es" con el proposito
   real del proyecto, y el bloque `roles:` de "Operating roles"
   (implementer/external_auditors — aunque sea un solo agente, decilo
   explicito, no lo dejes vacio). `CLAUDE.md` (al lado) no necesita edicion: es
   un shim generico apuntando a `AGENTS.md`.
2. **`LICENSE`** — decidi la licencia real (se mantiene MIT?
   otra? se borra porque el proyecto es privado?). Es una decision tuya, no la
   tome sola — preguntame si no esta claro.
3. **`governance/DECISION_LOG.md` — primera decision real** — reemplaza el
   formato de ejemplo D-000 con la primera decision real del proyecto (aunque
   sea solo "por que existe y que NO pretende ser").
4. **`README.md`** — titulo/identidad reales, borra cualquier aviso de
   "esto es un template" que haya quedado, y completa "Current status" en
   presente honesto (no describas capacidades que todavia son stubs).
5. **`config/settings.yaml`** — si el proyecto no necesita config declarativa todavia, borra toda la carpeta (no rompe nada en `release.py`).
6. **`scripts/agent_session.py`** — solo tiene sentido si mas de un agente/editor
   va a tocar el repo en paralelo. Si sos vos solo con un agente, borralo.
7. **`ui_language`** — confirma que `es` es el idioma correcto para
   textos de UI/errores de este proyecto.

El scaffold ya tiene el commit inicial `chore: initial template scaffold`.
Despues de resolver lo de arriba, verifica que el repo quede limpio:
```bash
python -m venv .venv
# activar segun tu shell (ver README.md para el comando exacto)
pip install -e ".[dev]"
python check.py
git status --short
```

## Reglas mientras haces esto

- No copies de vuelta politicas personales de permisos/guardrails de OpenCode a
  este repo salvo que el proyecto lo necesite — ya viven en tu config global.
- No asumas nada sobre el proposito del proyecto que no te haya dicho el/la
  duenx — preguntame.
- Revisa con `rg -n "project-template" .` que cualquier referencia restante sea
  intencional (ej. provenance).

## Despues de terminar

Borralo (`docs/FIRST-ADAPTATION.md`) — es solo para el arranque.
