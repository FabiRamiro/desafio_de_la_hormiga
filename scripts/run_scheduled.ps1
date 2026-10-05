$ErrorActionPreference = "Stop"

# La carpeta del proyecto se calcula a partir de la ubicacion de este script.
# De esta forma, la tarea funciona aunque Windows la inicie desde otra carpeta.
$projectDirectory = Split-Path -Parent $PSScriptRoot

# El Programador de tareas puede usar un PATH mas limitado que una terminal.
# Primero se intenta la ubicacion habitual de uv y despues se busca en PATH.
$uvPath = Join-Path $env:USERPROFILE ".local\bin\uv.exe"

if (-not (Test-Path -LiteralPath $uvPath)) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue

    if ($null -eq $uvCommand) {
        throw "No se encontro uv. Instala uv o ajusta `$uvPath en este script."
    }

    $uvPath = $uvCommand.Source
}

Push-Location $projectDirectory

try {
    # Fuerza UTF-8 en Python para que CrewAI pueda escribir acentos y emojis
    # aunque la tarea se ejecute sin una terminal interactiva.
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUNBUFFERED = "1"

    # Reduce codigos de color cuando se ejecuta desde el Programador de tareas.
    $env:NO_COLOR = "1"
    $env:FORCE_COLOR = "0"
    $env:TERM = "dumb"

    # uv prepara el entorno y CrewAI ejecuta la funcion run de main.py.
    & $uvPath run crewai run
    $crewExitCode = $LASTEXITCODE

    if ($crewExitCode -ne 0) {
        throw "CrewAI termino con el codigo de salida $crewExitCode."
    }
}
finally {
    Pop-Location
}
