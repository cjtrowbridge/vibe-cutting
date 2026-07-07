param(
    [switch]$AllowDownloads,
    [Parameter(Position = 0)]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArguments
)

$ErrorActionPreference = "Stop"
$PixiVersion = "0.72.0"
$MinimumGitVersion = [version]"2.31.0"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptRoot "..")).Path
$ToolsRoot = if ($env:VIBE_CUTTING_TOOLS_ROOT) { $env:VIBE_CUTTING_TOOLS_ROOT } else { Join-Path $RepoRoot ".tools" }
$Manifest = Join-Path $ScriptRoot "pixi.toml"
$Checksums = Join-Path $ScriptRoot "checksums\pixi-v$PixiVersion.sha256"

function Fail([string]$Message) {
    [Console]::Error.WriteLine("vibe-cutting bootstrap: $Message")
    exit 1
}

function Show-Usage {
    Write-Output "Usage: setup\bootstrap.ps1 [-AllowDownloads] <doctor|setup|verify|repair|report|run> [arguments]"
}

$RepoPrefix = $RepoRoot.TrimEnd('\') + '\'
if (-not $ToolsRoot.StartsWith($RepoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    Fail "tools root must remain inside the repository: $ToolsRoot"
}
if (Test-Path $ToolsRoot) {
    $ResolvedToolsRoot = (Resolve-Path $ToolsRoot).Path
    if (-not $ResolvedToolsRoot.StartsWith($RepoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Fail "tools root resolves outside the repository: $ToolsRoot"
    }
}

function Verify-Git {
    $Git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $Git) { Fail "Git $MinimumGitVersion or newer is required" }
    $VersionText = (& git --version) -replace '^git version\s+', ''
    $NormalizedVersionText = (($VersionText -replace '[^0-9.].*$', '').TrimEnd('.'))
    try { $Version = [version]$NormalizedVersionText } catch { Fail "unable to parse Git version: $VersionText" }
    if ($Version -lt $MinimumGitVersion) { Fail "Git $Version is too old; Git $MinimumGitVersion or newer is required" }
    return $Version.ToString()
}

function Detect-Platform {
    if (-not [Environment]::Is64BitOperatingSystem) { Fail "unsupported Windows architecture: 32-bit" }
    if ([Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne [Runtime.InteropServices.Architecture]::X64) {
        Fail "unsupported Windows architecture: $([Runtime.InteropServices.RuntimeInformation]::OSArchitecture)"
    }
    return @{
        Id = "windows-x86_64"
        Asset = "pixi-x86_64-pc-windows-msvc.exe"
        Url = "https://github.com/prefix-dev/pixi/releases/download/v$PixiVersion/pixi-x86_64-pc-windows-msvc.exe"
    }
}

function Get-ExpectedChecksum([string]$Asset) {
    foreach ($Line in Get-Content $Checksums) {
        $Parts = $Line -split '\s+', 2
        if ($Parts.Count -eq 2 -and $Parts[1].Trim() -eq $Asset) { return $Parts[0].ToLowerInvariant() }
    }
    Fail "no checksum recorded for $Asset"
}

function Configure-Pixi {
    $Paths = @(
        "config", "cache\pixi", "environments", "logs",
        "reports\host-readiness", "staging", "tmp", "pixi-home"
    )
    foreach ($Path in $Paths) { New-Item -ItemType Directory -Force -Path (Join-Path $ToolsRoot $Path) | Out-Null }
    $ConfigPath = Join-Path $ToolsRoot "config\pixi.toml"
    $EnvironmentPath = (Join-Path $ToolsRoot "environments").Replace('\', '/')
    $CachePath = (Join-Path $ToolsRoot "cache\pixi").Replace('\', '/')
    @"
detached-environments = "$EnvironmentPath"

[cache]
root = "$CachePath"
detached-environments = "$EnvironmentPath"
netfs-redirect = "never"
"@ | Set-Content -Encoding UTF8 $ConfigPath
    Activate-Pixi
}

function Activate-Pixi {
    $ConfigPath = Join-Path $ToolsRoot "config\pixi.toml"
    if (-not (Test-Path $ConfigPath -PathType Leaf)) { Fail "managed Pixi configuration is missing; run setup first" }
    $env:PIXI_HOME = Join-Path $ToolsRoot "pixi-home"
    $env:PIXI_CACHE_DIR = Join-Path $ToolsRoot "cache\pixi"
    $env:PIXI_CONFIG_FILE = $ConfigPath
    $env:PIXI_CACHE_DETACHED_ENVIRONMENTS_DIR = Join-Path $ToolsRoot "environments"
    $env:PIXI_CACHE_NETFS_REDIRECT = "never"
    $env:VIBE_CUTTING_REPO_ROOT = $RepoRoot
    $env:VIBE_CUTTING_TOOLS_ROOT = $ToolsRoot
    $env:VIBE_CUTTING_PIXI_VERSION = $PixiVersion
}

function Verify-Manager($Platform) {
    $PixiBin = Join-Path $ToolsRoot "bin\pixi.exe"
    if (-not (Test-Path $PixiBin -PathType Leaf)) { return $false }
    $Expected = Get-ExpectedChecksum $Platform.Asset
    $Actual = (Get-FileHash -Algorithm SHA256 $PixiBin).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) { Fail "installed Pixi checksum mismatch: expected $Expected, got $Actual" }
    return $true
}

function Install-Manager($Platform) {
    if (Verify-Manager $Platform) { return }
    if (-not $AllowDownloads) { Fail "Pixi is not installed; rerun with -AllowDownloads after approving the pinned download" }
    New-Item -ItemType Directory -Force -Path (Join-Path $ToolsRoot "bin"), (Join-Path $ToolsRoot "staging") | Out-Null
    $Staged = Join-Path $ToolsRoot "staging\$($Platform.Asset).part"
    Remove-Item -Force -ErrorAction SilentlyContinue $Staged
    Invoke-WebRequest -UseBasicParsing -Uri $Platform.Url -OutFile $Staged
    $Expected = Get-ExpectedChecksum $Platform.Asset
    $Actual = (Get-FileHash -Algorithm SHA256 $Staged).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) {
        Remove-Item -Force $Staged
        Fail "downloaded Pixi checksum mismatch: expected $Expected, got $Actual"
    }
    Move-Item -Force $Staged (Join-Path $ToolsRoot "bin\pixi.exe")
    if (-not (Verify-Manager $Platform)) { Fail "Pixi installation verification failed" }
}

function Run-StageTwo([string[]]$Arguments) {
    Activate-Pixi
    $PixiBin = Join-Path $ToolsRoot "bin\pixi.exe"
    if (-not (Test-Path $PixiBin -PathType Leaf)) { Fail "managed Pixi is unavailable; run setup first" }
    & $PixiBin run --manifest-path $Manifest --as-is -- python (Join-Path $ScriptRoot "bootstrap_host.py") @Arguments
    exit $LASTEXITCODE
}

$GitVersion = Verify-Git
$Platform = Detect-Platform

switch ($Command) {
    "doctor" {
        $ManagerState = if (Verify-Manager $Platform) { "ready" } else { "missing" }
        Write-Output "platform=$($Platform.Id)"
        Write-Output "git=$GitVersion"
        Write-Output "pixi=$ManagerState"
        Write-Output "tools_root=$ToolsRoot"
    }
    "setup" {
        Install-Manager $Platform
        if (-not (Test-Path (Join-Path $ToolsRoot "state\base-ready.json")) -and -not $AllowDownloads) {
            Fail "base environment is not ready; rerun with -AllowDownloads after approving dependency downloads"
        }
        Configure-Pixi
        & (Join-Path $ToolsRoot "bin\pixi.exe") install --manifest-path $Manifest --locked
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Run-StageTwo (@("setup") + $CommandArguments)
    }
    "repair" {
        Install-Manager $Platform
        if (-not $AllowDownloads) { Fail "repair may download locked dependencies; rerun with -AllowDownloads after approval" }
        Configure-Pixi
        & (Join-Path $ToolsRoot "bin\pixi.exe") install --manifest-path $Manifest --locked
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Run-StageTwo (@("repair") + $CommandArguments)
    }
    "verify" { if (-not (Verify-Manager $Platform)) { Fail "managed Pixi is unavailable; run setup first" }; Run-StageTwo (@("verify") + $CommandArguments) }
    "report" { if (-not (Verify-Manager $Platform)) { Fail "managed Pixi is unavailable; run setup first" }; Run-StageTwo (@("report") + $CommandArguments) }
    "run" {
        if (-not (Verify-Manager $Platform)) { Fail "managed Pixi is unavailable; run setup first" }
        if (-not $CommandArguments) { Fail "run requires a repository command" }
        $Delegated = if ($CommandArguments[0] -eq "--") {
            if ($CommandArguments.Count -gt 1) { $CommandArguments[1..($CommandArguments.Count - 1)] } else { @() }
        } else {
            $CommandArguments
        }
        Run-StageTwo (@("run", "--") + $Delegated)
    }
    { $_ -in @("help", "-h", "--help") } { Show-Usage }
    default { Show-Usage; Fail "unknown command: $Command" }
}
