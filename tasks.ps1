<#
.SYNOPSIS
    Thin Windows wrapper around the repository's `justfile`.
.DESCRIPTION
    Every task lives in ./justfile so humans (any OS), CI and coding agents
    share one interface. This script only forwards to `just`.

    Install just:  winget install Casey.Just   (or: cargo install just)

.EXAMPLE
    .\tasks.ps1                 # list tasks
    .\tasks.ps1 dev-core
    .\tasks.ps1 docker-logs ai_api
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

if (-not (Get-Command just -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "ERROR: 'just' is required. Install it with:  winget install Casey.Just" -ForegroundColor Red
    Write-Host "       Then re-run:  .\tasks.ps1 <task>" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Push-Location $PSScriptRoot
try {
    & just @Args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
