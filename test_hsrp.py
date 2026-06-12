#!/usr/bin/env python3
"""
test_hsrp.py - Script de validation du basculement HSRP
========================================================
TP BTS SIO - IRIS Paris
Protocole HSRP - Haute Disponibilité Cisco

Ce script valide le basculement automatique HSRP en :
  1. Effectuant un ping continu vers l'IP virtuelle HSRP
  2. Détectant la perte de connectivité (failover)
  3. Mesurant le temps de basculement
  4. Confirmant la reprise de service

Usage:
  python3 test_hsrp.py
  python3 test_hsrp.py --target 192.168.1.254 --duration 60
  python3 test_hsrp.py --target 192.168.1.254 --duration 120 --interval 0.5
"""

import subprocess
import platform
import time
import sys
import argparse
from datetime import datetime


# ============================================================
# CONFIGURATION PAR DEFAUT
# ============================================================
DEFAULT_TARGET   = "192.168.1.254"   # IP virtuelle HSRP
DEFAULT_DURATION = 60                 # Durée du test en secondes
DEFAULT_INTERVAL = 1.0                # Intervalle entre pings (secondes)
MAX_FAILOVER_TIME = 10.0              # Seuil d'alerte basculement (secondes)


# ============================================================
# COULEURS TERMINAL (ANSI)
# ============================================================
class Colors:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def green(text):  return f"{Colors.GREEN}{text}{Colors.RESET}"
def red(text):    return f"{Colors.RED}{text}{Colors.RESET}"
def yellow(text): return f"{Colors.YELLOW}{text}{Colors.RESET}"
def blue(text):   return f"{Colors.BLUE}{text}{Colors.RESET}"
def cyan(text):   return f"{Colors.CYAN}{text}{Colors.RESET}"
def bold(text):   return f"{Colors.BOLD}{text}{Colors.RESET}"


# ============================================================
# FONCTION PING
# ============================================================
def ping_host(host: str, timeout: int = 1) -> tuple[bool, float]:
    """
    Envoie un ping vers l'hôte cible.
    
    Returns:
        (success: bool, latency_ms: float)
    """
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), host]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        latency = (time.time() - start_time) * 1000  # en ms
        success = result.returncode == 0
        return success, latency
        
    except (subprocess.TimeoutExpired, Exception):
        return False, -1


# ============================================================
# AFFICHAGE EN-TETE
# ============================================================
def print_header(target: str, duration: int, interval: float):
    print()
    print(bold("=" * 60))
    print(bold(cyan("  TEST HSRP - Validation du Basculement Automatique")))
    print(bold("=" * 60))
    print(f"  Cible (IP Virtuelle HSRP) : {bold(target)}")
    print(f"  Durée du test             : {bold(str(duration))} secondes")
    print(f"  Intervalle ping           : {bold(str(interval))} seconde(s)")
    print(f"  Seuil alerte failover     : {bold(str(MAX_FAILOVER_TIME))} secondes")
    print(f"  Démarrage                 : {datetime.now().strftime('%H:%M:%S')}")
    print(bold("=" * 60))
    print()
    print("  Simuler le failover en coupant R1 (débrancher le câble")
    print("  ou faire 'shutdown' sur l'interface GigabitEthernet0/0)")
    print()
    print(bold("-" * 60))
    print(f"  {'N°':<5} {'Heure':<10} {'Statut':<12} {'Latence':<12} {'Info'}")
    print(bold("-" * 60))


# ============================================================
# FONCTION PRINCIPALE DE TEST
# ============================================================
def run_hsrp_test(target: str, duration: int, interval: float):
    """
    Lance le test de basculement HSRP.
    """
    print_header(target, duration, interval)
    
    # Statistiques
    stats = {
        "total":        0,
        "success":      0,
        "failed":       0,
        "failover_start": None,
        "failover_end":   None,
        "failover_time":  None,
        "latencies":    []
    }
    
    start_time   = time.time()
    in_failover  = False
    seq_num      = 0
    
    try:
        while (time.time() - start_time) < duration:
            seq_num += 1
            now = datetime.now().strftime("%H:%M:%S")
            
            success, latency = ping_host(target)
            stats["total"] += 1
            
            if success:
                # ---- PING REUSSI ----
                stats["success"] += 1
                stats["latencies"].append(latency)
                
                if in_failover:
                    # Fin du basculement
                    in_failover = False
                    stats["failover_end"] = time.time()
                    failover_time = stats["failover_end"] - stats["failover_start"]
                    stats["failover_time"] = failover_time
                    
                    status_icon = green("✅ OK")
                    info = green(f"⚡ REPRISE ! Failover terminé en {failover_time:.2f}s")
                    
                    if failover_time <= MAX_FAILOVER_TIME:
                        info += green(" ✓ DANS LES NORMES")
                    else:
                        info += yellow(f" ⚠ > {MAX_FAILOVER_TIME}s (vérifier timers)")
                else:
                    status_icon = green("✅ OK")
                    info = f"{latency:.1f} ms"
                    
            else:
                # ---- PING ECHOUE ----
                stats["failed"] += 1
                
                if not in_failover:
                    # Début du basculement
                    in_failover = True
                    stats["failover_start"] = time.time()
                    info = red("🔴 DEBUT FAILOVER - R1 injoignable, R2 prend le relais...")
                else:
                    elapsed = time.time() - stats["failover_start"]
                    info = yellow(f"⏳ Basculement en cours... {elapsed:.1f}s")
                    
                status_icon = red("❌ FAIL")
            
            # Affichage ligne
            latency_str = f"{latency:.1f}ms" if latency > 0 else "timeout"
            print(f"  {seq_num:<5} {now:<10} {status_icon:<12} {latency_str:<12} {info}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print()
        print(yellow("\n  Test interrompu par l'utilisateur (Ctrl+C)"))
    
    # ---- RAPPORT FINAL ----
    print()
    print(bold("=" * 60))
    print(bold(cyan("  RAPPORT FINAL")))
    print(bold("=" * 60))
    
    total_time = time.time() - start_time
    pkt_loss   = (stats["failed"] / stats["total"] * 100) if stats["total"] > 0 else 0
    avg_lat    = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
    
    print(f"  Durée totale      : {total_time:.1f}s")
    print(f"  Pings envoyés     : {stats['total']}")
    print(f"  Pings réussis     : {green(str(stats['success']))}")
    print(f"  Pings échoués     : {red(str(stats['failed']))}")
    print(f"  Perte de paquets  : {pkt_loss:.1f}%")
    print(f"  Latence moyenne   : {avg_lat:.1f} ms")
    print()
    
    if stats["failover_time"] is not None:
        ft = stats["failover_time"]
        print(f"  ⚡ Temps de basculement : {bold(f'{ft:.2f}s')}", end="")
        if ft <= 3.0:
            print(f"  {green('✅ EXCELLENT (< 3s)')} ")
        elif ft <= MAX_FAILOVER_TIME:
            print(f"  {green(f'✅ OK (< {MAX_FAILOVER_TIME}s)')}")
        else:
            print(f"  {red(f'❌ LENT (> {MAX_FAILOVER_TIME}s) - vérifier timers HSRP')}")
    else:
        print(f"  {yellow('ℹ️  Aucun basculement détecté pendant le test')}")
        print(f"     Pour tester : couper R1 pendant l'exécution du script")
    
    print()
    print(bold("=" * 60))
    
    # Verdict final
    if stats["failover_time"] and stats["failover_time"] <= MAX_FAILOVER_TIME:
        print(bold(green("  ✅ TEST REUSSI - HSRP opérationnel !")))
    elif stats["failover_time"]:
        print(bold(yellow("  ⚠️  TEST PARTIEL - Basculement lent, vérifier config")))
    else:
        print(bold(blue("  ℹ️  TEST INCOMPLET - Aucun failover déclenché")))
    
    print(bold("=" * 60))
    print()


# ============================================================
# POINT D'ENTREE
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script de validation du basculement HSRP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python3 test_hsrp.py
  python3 test_hsrp.py --target 192.168.1.254 --duration 60
  python3 test_hsrp.py --target 192.168.1.254 --duration 120 --interval 0.5
        """
    )
    
    parser.add_argument(
        "--target", "-t",
        default=DEFAULT_TARGET,
        help=f"IP virtuelle HSRP (défaut: {DEFAULT_TARGET})"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Durée du test en secondes (défaut: {DEFAULT_DURATION})"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=DEFAULT_INTERVAL,
        help=f"Intervalle entre pings en secondes (défaut: {DEFAULT_INTERVAL})"
    )
    
    args = parser.parse_args()
    
    run_hsrp_test(
        target=args.target,
        duration=args.duration,
        interval=args.interval
    )
