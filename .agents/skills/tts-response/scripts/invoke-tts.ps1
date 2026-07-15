[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $InputFile,

    [string] $ConfigFile = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-ExistingFile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $PathValue,
        [Parameter(Mandatory = $true)]
        [string] $Label
    )

    $expanded = [Environment]::ExpandEnvironmentVariables($PathValue)
    if (-not (Test-Path -LiteralPath $expanded -PathType Leaf)) {
        throw "$Label does not exist: $expanded"
    }

    return (Resolve-Path -LiteralPath $expanded).Path
}

function Quote-ProcessArgument {
    param([AllowEmptyString()][string] $Value)

    if ($null -eq $Value) {
        return '""'
    }

    # Sufficient for typical Windows paths and flag values used by TTS runners.
    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

if ($null -eq $ConfigFile -or $ConfigFile -eq "") {
    $ConfigFile = Join-Path $PSScriptRoot 'tts.config.psd1'
}

if (-not (Test-Path -LiteralPath $ConfigFile -PathType Leaf)) {
    throw "TTS config was not found: $ConfigFile"
}

$config = Import-PowerShellDataFile -LiteralPath $ConfigFile

if (-not $config.ContainsKey('Enabled') -or -not [bool]$config.Enabled) {
    Write-Host 'TTS runner is disabled in tts.config.psd1.'
    exit 0
}

$resolvedInput = Resolve-ExistingFile -PathValue $InputFile -Label 'Input file'

if (-not $config.ContainsKey('RunnerPath') -or [string]::IsNullOrWhiteSpace([string]$config.RunnerPath)) {
    throw 'RunnerPath is missing in tts.config.psd1.'
}

$runnerPath = Resolve-ExistingFile -PathValue ([string]$config.RunnerPath) -Label 'Runner'

if ($config.ContainsKey('WorkingDirectory') -and
    -not [string]::IsNullOrWhiteSpace([string]$config.WorkingDirectory)) {
    $workingDirectory = [Environment]::ExpandEnvironmentVariables([string]$config.WorkingDirectory)
    if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) {
        throw "WorkingDirectory does not exist: $workingDirectory"
    }
    $workingDirectory = (Resolve-Path -LiteralPath $workingDirectory).Path
}
else {
    $workingDirectory = Split-Path -Parent $runnerPath
}

$runnerArguments = @()
if ($config.ContainsKey('Arguments') -and $null -ne $config.Arguments) {
    foreach ($argument in @($config.Arguments)) {
        $runnerArguments += ([string]$argument).Replace('{input}', $resolvedInput)
    }
}

$runInBackground = $config.ContainsKey('RunInBackground') -and [bool]$config.RunInBackground
$hiddenWindow = $config.ContainsKey('HiddenWindow') -and [bool]$config.HiddenWindow
$extension = [System.IO.Path]::GetExtension($runnerPath).ToLowerInvariant()

if ($extension -eq '.ps1') {
    $hostExecutable = if ($PSVersionTable.PSEdition -eq 'Core') { 'pwsh.exe' } else { 'powershell.exe' }
    $processArguments = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $runnerPath
    ) + $runnerArguments
}
else {
    $hostExecutable = $runnerPath
    $processArguments = $runnerArguments
}

if ($runInBackground) {
    $argumentLine = ($processArguments | ForEach-Object { Quote-ProcessArgument -Value $_ }) -join ' '
    $cmdLine = "`"$hostExecutable`" $argumentLine"

    # Sử dụng WMI/CIM để tạo tiến trình độc lập hoàn toàn khỏi Job Object của cha
    try {
        $si = $null
        if ($hiddenWindow) {
            $si = New-CimInstance -ClassName Win32_ProcessStartup -Property @{ ShowWindow = [uint16]0 } -ClientOnly
        }
        
        $wmiArgs = @{
            CommandLine = $cmdLine
            CurrentDirectory = $workingDirectory
        }
        if ($null -ne $si) {
            $wmiArgs.ProcessStartupInformation = $si
        }

        $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments $wmiArgs
        if ($result.ReturnValue -eq 0) {
            Write-Host "TTS runner started via WMI. ProcessId: $($result.ProcessId)"
            exit 0
        }
    } catch {
        # Bỏ qua lỗi và fallback xuống dưới
    }

    # Cơ chế dự phòng (Fallback) nếu WMI không chạy được
    $startParams = @{
        FilePath         = $hostExecutable
        ArgumentList     = $argumentLine
        WorkingDirectory = $workingDirectory
        PassThru         = $true
    }
    if ($hiddenWindow) {
        $startParams.WindowStyle = 'Hidden'
    }
    $process = Start-Process @startParams
    Write-Host "TTS runner started via Start-Process fallback. PID: $($process.Id)"
    exit 0
}

Push-Location -LiteralPath $workingDirectory
try {
    & $hostExecutable @processArguments
    $exitCode = $LASTEXITCODE

    if ($null -ne $exitCode -and $exitCode -ne 0) {
        throw "TTS runner exited with code $exitCode."
    }
}
finally {
    Pop-Location
}

Write-Host 'TTS runner completed successfully.'
