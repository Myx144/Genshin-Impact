[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [ValidateSet("zip", "7z")]
    [string]$Format = "zip"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputRoot = Join-Path $repositoryRoot "dist"
$packageName = "GenshinDamageCalculator-$Version"
$stagePath = Join-Path $outputRoot $packageName
$archivePath = Join-Path $outputRoot "$packageName.$Format"

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

if (Test-Path -LiteralPath $stagePath) {
    $resolvedStage = (Resolve-Path -LiteralPath $stagePath).Path
    $resolvedOutput = (Resolve-Path -LiteralPath $outputRoot).Path
    if (-not $resolvedStage.StartsWith($resolvedOutput + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a staging path outside dist: $resolvedStage"
    }
    Remove-Item -LiteralPath $resolvedStage -Recurse -Force
}
if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

New-Item -ItemType Directory -Path $stagePath | Out-Null
$recognitionPath = Join-Path $stagePath "recognition"
New-Item -ItemType Directory -Path $recognitionPath | Out-Null

function Copy-ReleaseFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Release source is missing: $Source"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

# QML frontend, runtime icon, and OCR code.
foreach ($name in @("main.py", "Main.qml", "AtkPage.qml", "AppButton.qml", "AppCheckBox.qml", "Columbina.ico", "requirements.txt", "start.bat")) {
    Copy-ReleaseFile (Join-Path $repositoryRoot "qml_prototype\$name") (Join-Path $stagePath $name)
}
foreach ($name in @("__init__.py", "ugc_panel.py", "README.md")) {
    Copy-ReleaseFile (Join-Path $repositoryRoot "qml_prototype\recognition\$name") (Join-Path $recognitionPath $name)
}

# The QML frontend imports these two calculation-backend files at runtime.
foreach ($name in @("damage_calculator.py", "atk_calculator.py")) {
    Copy-ReleaseFile (Join-Path $repositoryRoot $name) (Join-Path $stagePath $name)
}
Copy-ReleaseFile (Join-Path $repositoryRoot "qml_prototype\RELEASE_README.md") (Join-Path $stagePath "README.md")

if ($Format -eq "zip") {
    Compress-Archive -LiteralPath $stagePath -DestinationPath $archivePath -CompressionLevel Optimal
} else {
    $sevenZip = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if (-not $sevenZip) {
        $candidate = "C:\Program Files\7-Zip\7z.exe"
        if (Test-Path -LiteralPath $candidate) {
            $sevenZip = Get-Item -LiteralPath $candidate
        }
    }
    if (-not $sevenZip) {
        throw "7z.exe was not found. Install 7-Zip or run with -Format zip."
    }
    & $sevenZip.Source a -t7z $archivePath $stagePath | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Release package created: $archivePath"
Write-Host "Upload this file as a GitHub Release asset."
