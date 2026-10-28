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

def format_duration(seconds):
    mins, secs = divmod(seconds, 60)
    if mins > 0:
        return f"{int(mins)}m {secs:04.1f}s ({seconds:.1f}s)"
    return f"{seconds:.1f}s"

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
        status = "OK" if ret.returncode == 0 else f"ERRORE (code {ret.returncode})"
        print(f"\n[{status}] COMPLETATO: {step_name} in {format_duration(elapsed)}", flush=True)
        return ret.returncode, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[ERRORE] durante {step_name} dopo {format_duration(elapsed)}: {e}", flush=True)
        return -1, elapsed

def main():
    total_start = time.time()
    print("*"*70)
    print("SCANSIONE COMPLETA DEI 3 PORTALI IMMOBILIARI")
    print("   1. Idealista.it")
    print("   2. Engel & Volkers")
    print("   3. Immobiliare.it")
    print("   4. Aggiornamento Tabella (dump_table_v4.py)")
    print("*"*70, flush=True)

    durations = {}

    # 1. Idealista
    code, dur = run_step("1/4 Scraper Idealista", "scrape_idealista.py")
    durations["Idealista.it"] = (dur, code)

    # 2. Engel & Volkers
    code, dur = run_step("2/4 Scraper Engel & Volkers", "scrape_ev.py")
    durations["Engel & Völkers"] = (dur, code)

    # 3. Immobiliare.it
    code, dur = run_step("3/4 Scraper Immobiliare.it", "scrape_immobiliare.py")
    durations["Immobiliare.it"] = (dur, code)

    # 4. Rigenerazione tabella
    code, dur = run_step("4/4 Aggiornamento Tabella Poligono", "dump_table_v4.py")
    durations["Tabella & Datalake"] = (dur, code)

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

    total_elapsed = time.time() - total_start

    print("\n" + "="*70)
    print("📊 RIEPILOGO TEMPI DI SCANSIONE PER CIASCUN PORTALE")
    print("="*70)
    for name, (dur, code) in durations.items():
        status_str = "✅ OK" if code == 0 else f"❌ ERR ({code})"
        print(f" • {name:<22}: {format_duration(dur):<18} [{status_str}]")
    print("-" * 70)
    print(f" ⏱️  TEMPO TOTALE SCANSIONE: {format_duration(total_elapsed)}")
    print("="*70, flush=True)

if __name__ == "__main__":
    main()
