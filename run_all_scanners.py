import sys
import os
import shutil
import subprocess
import time
import json

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

    # ── Leggi statistiche di scansione dai file JSON prodotti dagli scraper ──
    STATS_FILES = {
        "Idealista.it":    "scan_stats_idealista.json",
        "Engel & Völkers": "scan_stats_ev.json",
        "Immobiliare.it":  "scan_stats_immobiliare.json",
    }
    scan_stats = {}
    for portale, stats_file in STATS_FILES.items():
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    scan_stats[portale] = json.load(f)
            except Exception:
                scan_stats[portale] = {}
        else:
            scan_stats[portale] = {}

    # ── Sanity check: avvisa se uno scraper ha scansionato troppo poco ──────
    print("\n" + "="*70)
    print("🔍 VERIFICA QUALITÀ SCANSIONE")
    print("="*70)
    warnings_found = False
    for portale, stats in scan_stats.items():
        pagine = stats.get("pagine_scansionate", None)
        grezzi = stats.get("annunci_grezzi", None)
        durata = stats.get("durata_secondi", None)
        code = durations.get(portale, (0, 0))[1]

        if pagine is not None and grezzi is not None and durata is not None:
            # Avvisa se: scansione completata (exit 0) ma pochissime pagine in poco tempo
            if code == 0 and pagine <= 1 and durata < 60:
                print(f"  ⚠️  ATTENZIONE: {portale} ha scansionato solo {pagine} pagina/e "
                      f"in {durata:.0f}s con {grezzi} annunci grezzi. "
                      f"Probabile errore di paginazione — verificare!")
                warnings_found = True
            elif code == 0 and grezzi == 0:
                print(f"  ⚠️  ATTENZIONE: {portale} non ha trovato nessun annuncio grezzo. "
                      f"Possibile blocco anti-bot o cambio struttura pagina.")
                warnings_found = True
            else:
                print(f"  ✅ {portale}: {pagine} pagine scansionate, {grezzi} annunci grezzi "
                      f"→ {stats.get('annunci_validi', 'N/D')} validi. OK.")
        else:
            # Nessun file stats disponibile
            dur_v, code_v = durations.get(portale, (0, -1))
            if code_v != 0:
                print(f"  ❌ {portale}: terminato con errore (code {code_v}).")
            else:
                print(f"  ℹ️  {portale}: statistiche dettagliate non disponibili.")

    if not warnings_found:
        print("\n  Nessuna anomalia rilevata. Tutte le scansioni sembrano corrette.")

    print("\n" + "="*70)
    print("📊 RIEPILOGO TEMPI DI SCANSIONE PER CIASCUN PORTALE")
    print("="*70)

    # Intestazione tabella adattiva: aggiungi colonne stats se disponibili
    has_stats = any(scan_stats.values())
    if has_stats:
        print(f"  {'Portale':<22} {'Durata':<18} {'Pagine':>7} {'Grezzi':>7} {'Validi':>7}  Esito")
        print(f"  {'-'*22} {'-'*18} {'-'*7} {'-'*7} {'-'*7}  {'-----'}")
    for name, (dur, code) in durations.items():
        status_str = "✅ OK" if code == 0 else f"❌ ERR ({code})"
        stats = scan_stats.get(name, {})
        if has_stats:
            pagine_s = str(stats.get("pagine_scansionate", "N/D")) if stats else "N/D"
            grezzi_s = str(stats.get("annunci_grezzi",      "N/D")) if stats else "N/D"
            validi_s = str(stats.get("annunci_validi",       "N/D")) if stats else "N/D"
            print(f"  {name:<22} {format_duration(dur):<18} {pagine_s:>7} {grezzi_s:>7} {validi_s:>7}  [{status_str}]")
        else:
            print(f" • {name:<22}: {format_duration(dur):<18} [{status_str}]")

    print("-" * 70)
    print(f" ⏱️  TEMPO TOTALE SCANSIONE: {format_duration(total_elapsed)}")
    print("="*70, flush=True)

if __name__ == "__main__":
    main()
