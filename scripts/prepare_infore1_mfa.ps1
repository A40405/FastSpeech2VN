param(
    [string]$DatasetId = "doof-ferb/infore1_25hours",
    [string]$Split = "train",
    [string]$PythonExe = "D:\Anaconda\envs\llama_gpu\python.exe",
    [string]$MfaExe = "mfa",
    [int]$NumJobs = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& $PythonExe .\scripts\download_infore1_dataset.py --dataset $DatasetId --split $Split --output-dir .\corpus\infore1_25hours
& $PythonExe .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --g2p-train-path .\mfa_assets\infore1_vi_g2p.tsv --wordlist-path .\mfa_assets\infore1_vi.wordlist --symbol-map-path .\mfa_assets\infore1_vi_symbol_map.tsv
& $PythonExe .\scripts\train_vietnamese_g2p.py --mfa $MfaExe --dictionary-path .\mfa_assets\infore1_vi.dict --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
& $PythonExe .\scripts\run_mfa_train_alignment.py --mfa $MfaExe --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs $NumJobs --single-speaker --overwrite
& $PythonExe .\scripts\validate_alignment.py --config .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\scripts\check_phoneset.py --config .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\scripts\build_infore1_clean_subset.py --config .\config\InfoRe1_25hours\preprocess.yaml
& $PythonExe .\scripts\audit_infore1_preprocessed.py --root .\preprocessed_data\InfoRe1
