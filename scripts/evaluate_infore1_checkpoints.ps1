param(
    [string]$PythonExe = "python",
    [int[]]$Steps = @(8000, 16000, 24000),
    [string]$PreprocessConfig = ".\config\InfoRe1_25hours\preprocess.yaml",
    [string]$ModelConfig = ".\config\InfoRe1_25hours\model.yaml",
    [string]$TrainConfig = ".\config\InfoRe1_25hours\train.yaml",
    [string]$ResultRoot = ".\output\result\InfoRe1",
    [string]$ReviewRoot = ".\output\result\InfoRe1_eval"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sentences = @(
    @{ Index = "01"; Text = "xin chào bạn" },
    @{ Index = "02"; Text = "mời bạn ngồi xuống" },
    @{ Index = "03"; Text = "hôm nay trời đẹp" }
)

foreach ($step in $Steps) {
    $stepDir = Join-Path $ReviewRoot ("step_{0}" -f $step)
    New-Item -ItemType Directory -Force -Path $stepDir | Out-Null

    foreach ($sample in $sentences) {
        $text = $sample.Text
        & $PythonExe .\synthesize.py --mode single --text $text --restore_step $step -p $PreprocessConfig -m $ModelConfig -t $TrainConfig

        $basename = $text.Substring(0, [Math]::Min(100, $text.Length))
        $sourceWav = Join-Path $ResultRoot ($basename + ".wav")
        $sourcePng = Join-Path $ResultRoot ($basename + ".png")
        $targetStem = "{0}_{1}" -f $sample.Index, ($basename -replace "\s+", "-")

        if (Test-Path -LiteralPath $sourceWav) {
            Copy-Item -LiteralPath $sourceWav -Destination (Join-Path $stepDir ($targetStem + ".wav")) -Force
        }
        if (Test-Path -LiteralPath $sourcePng) {
            Copy-Item -LiteralPath $sourcePng -Destination (Join-Path $stepDir ($targetStem + ".png")) -Force
        }
    }
}

Write-Host "Saved checkpoint review files under $ReviewRoot"
