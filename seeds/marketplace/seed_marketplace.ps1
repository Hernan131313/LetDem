param(
  [string]$Settings = ""
)

# Ejecuta el seed del marketplace de forma consistente desde cualquier carpeta
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManagePyDir = Join-Path $ScriptDir "..\.."

Push-Location $ManagePyDir
try {
  if ($Settings -ne "") { $env:DJANGO_SETTINGS_MODULE = $Settings }
  python manage.py populate_marketplace
}
finally {
  Pop-Location
}
