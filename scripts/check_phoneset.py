import argparse
import csv
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from text.vietnamese import FASTSPEECH_SYMBOL_MAP, SILENCE_IPA_TOKENS, VIETNAMESE_IPA_TOKENS
from utils.io import atomic_write_json, utc_timestamp


NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")
DISAMBIGUATION_SYMBOL_RE = re.compile(r"^#\d+$")
EPSILON_SYMBOLS = {"<eps>", "<epsilon>"}


def _is_numeric_token(token):
    return bool(NUMERIC_TOKEN_RE.match(token))


def _is_symbolic_phone_token(token):
    return bool(token) and not _is_numeric_token(token)


def _is_technical_model_symbol(token):
    return token in EPSILON_SYMBOLS or bool(DISAMBIGUATION_SYMBOL_RE.match(token))


def _extract_dictionary_phone_tokens(parts):
    if len(parts) < 2:
        return []

    phone_start = 1
    while phone_start < len(parts) and _is_numeric_token(parts[phone_start]):
        phone_start += 1

    return [token for token in parts[phone_start:] if _is_symbolic_phone_token(token)]


def load_dictionary_phones(dictionary_path):
    phones = set()
    with open(dictionary_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            for phone in _extract_dictionary_phone_tokens(parts):
                phones.add(phone)
    return phones


def load_symbol_map(symbol_map_path):
    rows = []
    with open(symbol_map_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def load_model_zip_phones(zip_path):
    if not os.path.exists(zip_path):
        return None, f"missing file: {zip_path}"

    phones = set()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            if any(name.endswith("phones.sym") for name in names):
                target = next(name for name in names if name.endswith("phones.sym"))
                with zf.open(target) as f:
                    for raw_line in f:
                        parts = raw_line.decode("utf-8").strip().split()
                        if not parts:
                            continue
                        token = parts[0]
                        if _is_technical_model_symbol(token):
                            continue
                        phones.add(token)
            elif any(name.endswith("meta.json") for name in names):
                target = next(name for name in names if name.endswith("meta.json"))
                with zf.open(target) as f:
                    meta = json.load(f)
                for value in meta.values():
                    if isinstance(value, list):
                        phones.update(
                            str(item)
                            for item in value
                            if isinstance(item, str) and not _is_technical_model_symbol(str(item))
                        )
            return phones, None
    except Exception as exc:
        return None, str(exc)

    return set(), None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/InfoRe1_25hours/preprocess.yaml",
        help="Path to preprocess.yaml",
    )
    parser.add_argument(
        "--symbol-map-path",
        default="mfa_assets/infore1_vi_symbol_map.tsv",
        help="Path to IPA symbol map TSV",
    )
    parser.add_argument(
        "--acoustic-model-path",
        default="mfa_assets/infore1_vi_acoustic_model.zip",
        help="Path to MFA acoustic model zip",
    )
    parser.add_argument(
        "--report-path",
        default="mfa_assets/phoneset_report.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    config = yaml.load(open(args.config, "r", encoding="utf-8"), Loader=yaml.FullLoader)
    dictionary_path = config["path"]["lexicon_path"]
    g2p_model_path = config["path"]["g2p_model_path"]

    text_phones = set(VIETNAMESE_IPA_TOKENS) | set(SILENCE_IPA_TOKENS)
    dictionary_phones = load_dictionary_phones(dictionary_path)
    symbol_rows = load_symbol_map(args.symbol_map_path)
    symbol_map_phones = {row["ipa_phone"] for row in symbol_rows}
    symbol_map_symbols = {row["fastspeech_symbol"] for row in symbol_rows}
    g2p_phones, g2p_error = load_model_zip_phones(g2p_model_path)
    acoustic_phones, acoustic_error = load_model_zip_phones(args.acoustic_model_path)

    report = {
        "generated_at": utc_timestamp(),
        "inputs": {
            "dictionary_path": dictionary_path,
            "g2p_model_path": g2p_model_path,
            "acoustic_model_path": args.acoustic_model_path,
            "symbol_map_path": args.symbol_map_path,
        },
        "summary": {
            "text_phone_count": len(text_phones),
            "dictionary_phone_count": len(dictionary_phones),
            "symbol_map_phone_count": len(symbol_map_phones),
            "errors": 0,
        },
        "errors": [],
        "warnings": [],
        "checks": {},
    }

    checks = report["checks"]
    checks["dictionary_only_phones"] = sorted(dictionary_phones - text_phones)
    checks["text_only_phones"] = sorted(text_phones - dictionary_phones)
    checks["symbol_map_missing_phones"] = sorted(text_phones - symbol_map_phones)
    checks["symbol_map_extra_phones"] = sorted(symbol_map_phones - text_phones)
    checks["missing_fastspeech_symbols"] = sorted(
        "@" + phone for phone in text_phones if "@" + phone not in symbol_map_symbols
    )

    if checks["dictionary_only_phones"]:
        report["errors"].append(
            {
                "type": "dictionary_oov_phones",
                "phones": checks["dictionary_only_phones"],
            }
        )
    if checks["symbol_map_missing_phones"] or checks["symbol_map_extra_phones"]:
        report["errors"].append(
            {
                "type": "symbol_map_inconsistent",
                "missing": checks["symbol_map_missing_phones"],
                "extra": checks["symbol_map_extra_phones"],
            }
        )
    if checks["missing_fastspeech_symbols"]:
        report["errors"].append(
            {
                "type": "fastspeech_symbol_missing",
                "symbols": checks["missing_fastspeech_symbols"],
            }
        )

    if g2p_error:
        report["warnings"].append({"type": "g2p_model_warning", "message": g2p_error})
    else:
        checks["g2p_model_extra_phones"] = sorted(g2p_phones - text_phones)
        if checks["g2p_model_extra_phones"]:
            report["errors"].append(
                {
                    "type": "g2p_model_inconsistent",
                    "phones": checks["g2p_model_extra_phones"],
                }
            )

    if acoustic_error:
        report["errors"].append(
            {"type": "acoustic_model_error", "message": acoustic_error}
        )
    else:
        checks["acoustic_model_extra_phones"] = sorted(acoustic_phones - text_phones)
        if checks["acoustic_model_extra_phones"]:
            report["errors"].append(
                {
                    "type": "acoustic_model_inconsistent",
                    "phones": checks["acoustic_model_extra_phones"],
                }
            )

    report["summary"]["errors"] = len(report["errors"])
    atomic_write_json(report, args.report_path)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Saved phoneset report to {args.report_path}")

    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
