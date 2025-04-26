# romlib - Una librería para gestionar ROMs de videojuegos de 8 y 16 bits
# Copyright (C) 2025 Arbotti Juan
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General de GNU publicada por
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (cuando prefieras) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; incluso sin la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.
# Consulta la Licencia Pública General de GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General de GNU
# junto con este programa. Si no, consulta <https://www.gnu.org/licenses/>.


from . import errors, tags, roms

__all__ = ["errors", "tags", "roms", "db"]

def __dir__():
    return __all__

def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"Module 'romlib' has no attribute '{name}'")
    return globals()[name]