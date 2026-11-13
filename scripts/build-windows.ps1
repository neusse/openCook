param([string]$ProjectRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$jdk = Get-ChildItem -LiteralPath (Join-Path $env:ProgramFiles 'Microsoft') -Directory -Filter 'jdk-17*' |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $jdk) { throw 'Microsoft OpenJDK 17 is required for this build.' }
if (-not $env:ANDROID_HOME) { throw 'ANDROID_HOME is not set.' }
if (-not (Test-Path -LiteralPath (Join-Path $env:ANDROID_HOME 'platforms\android-37.0'))) {
    throw 'Android SDK Platform 37.0 is missing.'
}
$env:JAVA_HOME = $jdk.FullName
$env:Path = (Join-Path $env:JAVA_HOME 'bin') + [IO.Path]::PathSeparator + $env:Path
Push-Location $root
try {
    & .\gradlew.bat assembleDebug
    if ($LASTEXITCODE -ne 0) { throw "Gradle build failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location }
