$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$dependencyDir = Join-Path $projectRoot 'work/deps'
New-Item -ItemType Directory -Force $dependencyDir | Out-Null
if (-not (Test-Path (Join-Path $projectRoot 'work/DiffTGen/build.xml'))) {
    git -C $projectRoot submodule update --init work/DiffTGen
    if ($LASTEXITCODE -ne 0) { throw 'DiffTGen submodule setup failed.' }
}
$downloads = @{
    'jdk8-complete.tar.gz' = 'https://cdn.azul.com/zulu/bin/zulu8.94.0.17-ca-jdk8.0.492-linux_x64.tar.gz'
    'ant.jar' = 'https://repo.maven.apache.org/maven2/org/apache/ant/ant/1.10.15/ant-1.10.15.jar'
    'ant-launcher.jar' = 'https://repo.maven.apache.org/maven2/org/apache/ant/ant-launcher/1.10.15/ant-launcher-1.10.15.jar'
    'ant-junit.jar' = 'https://repo.maven.apache.org/maven2/org/apache/ant/ant-junit/1.10.15/ant-junit-1.10.15.jar'
    'commons-lang-2.3.jar' = 'https://repo.maven.apache.org/maven2/commons-lang/commons-lang/2.3/commons-lang-2.3.jar'
}
foreach ($item in $downloads.GetEnumerator()) {
    $destination = Join-Path $dependencyDir $item.Key
    if (-not (Test-Path $destination)) {
        & curl.exe --fail --location --max-time 600 $item.Value -o $destination
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $($item.Key). Remove the partial file before retrying." }
    }
}
$unixRoot = (& wsl -d Ubuntu-22.04 -- wslpath -a $projectRoot).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve project path in Ubuntu-22.04.' }
& wsl -d Ubuntu-22.04 -- bash "$unixRoot/outputs/reproduction/setup-local.sh"
if ($LASTEXITCODE -ne 0) { throw 'Project-local setup failed.' }
Write-Output "Ready. In WSL, cd to $unixRoot and run bash outputs/reproduction/run-single.sh --budget 180 --seed 2026102702"
