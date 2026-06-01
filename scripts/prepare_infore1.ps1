param(
    [string]$DatasetId = "doof-ferb/infore1_25hours",
    [string]$Split = "train",
    [string]$PythonExe = "D:\Anaconda\envs\llama_gpu\python.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& $PythonExe .\scripts\download_infore1_dataset.py --dataset $DatasetId --split $Split --output-dir .\corpus\infore1_25hours
& $PythonExe .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\scripts\bootstrap_textgrids.py --raw-root .\raw_data\InfoRe1 --output-root .\preprocessed_data\InfoRe1\TextGrid
& $PythonExe .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
