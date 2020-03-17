from pathlib import Path

PACK_DIR = Path(__file__).resolve().parent

def get_msdsl_header():
    return PACK_DIR / 'msdsl.sv'