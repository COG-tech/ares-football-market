$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$integrator = Join-Path $scriptRoot "integrate_open_match_data.py"

python $integrator --publish
