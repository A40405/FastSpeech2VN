param(
    [string]$DatasetId = "doof-ferb/infore1_25hours",
    [string]$Split = "train",
    [string]$PythonExe = "D:\Anaconda\envs\llama_gpu\python.exe",
    [string]$MfaExe = "mfa",
    [int]$NumJobs = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& $PythonExe .\scripts\prepare_infore1_mfa.ps1 -DatasetId $DatasetId -Split $Split -PythonExe $PythonExe -MfaExe $MfaExe -NumJobs $NumJobs
