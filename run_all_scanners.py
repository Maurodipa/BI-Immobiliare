import sys
import os
import shutil
import subprocess
import time

# Assicura compatibilita UTF-8 su Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_step(step_name, script_path):
    print("\n" + "="*70)
    print(f">> AVVIO: {step_name} ({script_path})")
    print("="*70, flush=True)
    start_time = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        ret = subprocess.run([sys.executable, script_path], check=False, env=env)
        elapsed = time.time() - start_time
        print(f"\n[OK] COMPLETATO: {step_name} in {elapsed:.1f}s (Exit code: {ret.returncode})", flush=True)
        return ret.returncode
    except Exception as e:
        print(f"\n[ERRORE] durante {step_name}: {e}", flush=True)
        return -1

def main():
    print("*"*70)
    print("SCANSIONE COMPLETA DEI 3 PORTALI IMMOBILIARI")
    print("   1. Idealista.it")
    print("   2. Engel & Volkers")
    print("   3. Immobiliare.it")
    print("   4. Aggiornamento Tabella (dump_table_v4.py)")
    print("*"*70, flush=True)

    # 1. Idealista
    run_step("1/4 Scraper Idealista", "scrape_idealista.py")

    # 2. Engel & Volkers
    run_step("2/4 Scraper Engel & Volkers", "scrape_ev.py")

    # 3. Immobiliare.it
    run_step("3/4 Scraper Immobiliare.it", "scrape_immobiliare.py")

    # 4. Rigenerazione tabella
    run_step("4/4 Aggiornamento Tabella Poligono", "dump_table_v4.py")

    # Sincronizzazione file tabella
    src_table = "tabella_poligono_categorizzata.md"
    dst_workspace = "tabella_poligono.md"
    dst_artifact = r"C:\Users\mauro\.gemini\antigravity\brain\175b7fe0-188c-4061-a9c8-745b4b82a986\tabella_poligono.md"

    if os.path.exists(src_table):
        shutil.copyfile(src_table, dst_workspace)
        print(f"[OK] Copiato su: {dst_workspace}")
        try:
            shutil.copyfile(src_table, dst_artifact)
            print(f"[OK] Copiato nell'artifact: {dst_artifact}")
        except Exception as e:
            print(f"[WARNING] Impossibile aggiornare artifact: {e}")

    print("\n" + "="*70)
    print("PROCEDURA COMPLETATA!")
    print("="*70, flush=True)

if __name__ == "__main__":
    main()
