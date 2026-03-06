# Marketplace seeds

Este directorio contiene utilidades para poblar la base de datos con datos de ejemplo del Marketplace.

Qué incluyen los "seeds"
- Datos mínimos: categorías, tiendas y productos de prueba.
- Están implementados como un comando de Django: `populate_marketplace`.

Uso
- Local (desde la carpeta `src/`):
  - `python manage.py populate_marketplace`
- Desde la raíz del repo:
  - `python src/manage.py populate_marketplace`
- En staging/producción (si tu servicio usa otro settings):
  - `DJANGO_SETTINGS_MODULE=letdem.settings.staging python manage.py populate_marketplace`

Scripts
- Windows PowerShell: `src/seeds/marketplace/seed_marketplace.ps1`
- Bash: `src/seeds/marketplace/seed_marketplace.sh`

Notas
- El comando es idempotente: usa `get_or_create` para no duplicar registros.
- Si necesitas resetear datos, hazlo con un comando separado (no incluido aquí).
