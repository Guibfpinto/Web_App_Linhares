@echo off
setlocal
title Compactar projeto_web (sem utilitarios do Banco de Dados)

REM ==========================================================
REM  Compacta a pasta deste .bat em um .zip, deixando de fora:
REM   - os utilitarios de Banco de Dados fora do app (ver_estrutura_banco.py, api.py)
REM   - arquivos .sql (schemas/dumps)
REM   - .git e __pycache__
REM
REM  INCLUIR_DB=1  -> os arquivos .db / .sqbpro VAO no zip
REM  INCLUIR_DB=0  -> os arquivos .db / .sqbpro ficam de fora
REM ==========================================================
set "INCLUIR_DB=1"

set "ALVO=%~dp0"
if "%ALVO:~-1%"=="\" set "ALVO=%ALVO:~0,-1%"
set "ESTE_BAT=%~nx0"

echo Compactando: %ALVO%
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-Content -LiteralPath '%~f0' -Raw; $p = ($c -split '\r?\n#PSSTART\r?\n')[-1]; Invoke-Expression $p"
echo.
pause
exit /b

#PSSTART
$ErrorActionPreference = 'Stop'
$root      = $env:ALVO
$incluirDb = $env:INCLUIR_DB -eq '1'
$esteBat   = $env:ESTE_BAT

# Utilitarios de banco que o app Streamlit nao usa
$scriptsBanco = @(
  'ver_estrutura_banco.py',
  'api.py'
)
# Arquivos do app que SEMPRE entram no zip, mesmo acessando o banco
$sempreIncluir = @(
  'api_football_client.py',
  'app.py',
  'utils.py',
  'monitoramento.py'
)
$incluidos = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($n in $sempreIncluir) { [void]$incluidos.Add($n) }

$excluidos = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($n in $scriptsBanco) { [void]$excluidos.Add($n) }

$pastaNome = Split-Path $root -Leaf
$stamp     = Get-Date -Format 'yyyy-MM-dd_HHmm'
$destino   = Join-Path $root ("Backup_{0}_{1}.zip" -f $pastaNome, $stamp)

$arquivos = Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object {
    $rel = $_.FullName.Substring($root.Length + 1)
    $ext = $_.Extension.ToLower()
    $incluidos.Contains($_.Name) -or -not (
        $rel -like '.git\*' -or
        $rel -like '__pycache__\*' -or $rel -like '*\__pycache__\*' -or
        $excluidos.Contains($_.Name) -or
        $ext -eq '.sql' -or
        (-not $incluirDb -and ($ext -eq '.db' -or $ext -eq '.sqbpro')) -or
        ($_.DirectoryName -eq $root -and ($_.Name -eq $esteBat -or $_.Name -like 'Backup_*.zip'))
    )
}

$total = @($arquivos).Count
Write-Host "Arquivos a compactar: $total"
Write-Host "Destino: $destino"
Write-Host ''

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($destino, 'Create')
$i = 0; $falhas = @()
try {
    foreach ($f in $arquivos) {
        $i++
        $rel = $f.FullName.Substring($root.Length + 1) -replace '\\', '/'
        try {
            [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, $rel, 'Optimal')
        } catch {
            $falhas += $rel
        }
        if ($i % 100 -eq 0 -or $i -eq $total) {
            Write-Progress -Activity 'Compactando' -Status "$i de $total" -PercentComplete (($i / [math]::Max($total,1)) * 100)
        }
    }
} finally {
    $zip.Dispose()
}
Write-Progress -Activity 'Compactando' -Completed

$mb = [math]::Round((Get-Item -LiteralPath $destino).Length / 1MB, 1)
Write-Host "Concluido! $($total - $falhas.Count) arquivos em $destino ($mb MB)" -ForegroundColor Green
if ($falhas.Count -gt 0) {
    Write-Host ''
    Write-Host "Nao foi possivel incluir $($falhas.Count) arquivo(s) (em uso ou sem permissao):" -ForegroundColor Yellow
    $falhas | ForEach-Object { Write-Host "  - $_" }
}
