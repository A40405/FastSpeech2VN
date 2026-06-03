import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_mfa_command(mfa_value):
    mfa_path = Path(mfa_value)
    if mfa_path.is_file():
        resolved = mfa_path.resolve()
        return str(resolved), str(resolved.parent)

    discovered = shutil.which(mfa_value)
    if discovered is None:
        raise SystemExit(
            "MFA executable not found. Install Montreal Forced Aligner first, for example via conda-forge."
        )
    resolved = Path(discovered).resolve()
    return str(resolved), str(resolved.parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mfa", default="mfa", help="MFA executable name or path")
    parser.add_argument(
        "--dictionary-path",
        default="mfa_assets/infore1_vi_g2p.tsv",
        help="Path to word<TAB>phones training data or pronunciation dictionary",
    )
    parser.add_argument(
        "--output-model-path",
        default="mfa_assets/infore1_vi_g2p_model.zip",
        help="Path to the exported MFA G2P model",
    )
    parser.add_argument("--validate", action="store_true", help="Run MFA validation during training")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing G2P model")
    args = parser.parse_args()

    mfa_executable, mfa_bin_dir = resolve_mfa_command(args.mfa)

    dictionary_path = Path(args.dictionary_path)
    output_model_path = Path(args.output_model_path)
    output_model_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        mfa_executable,
        "train_g2p",
        str(dictionary_path),
        str(output_model_path),
        "--clean",
    ]
    if args.validate:
        command.append("--validate")
    if args.overwrite:
        command.append("--overwrite")

    env = os.environ.copy()
    env["PATH"] = mfa_bin_dir + os.pathsep + env.get("PATH", "")

    print("Running:", " ".join(command))
    completed = subprocess.run(command, env=env)
    sys.exit(completed.returncode)


if __name__ == "__main__":
    main()
