"""
modules/scan/scanner.py — System health scanner.
Read-only checks: disk, RAM, load, services, updates.
"""

import subprocess, shutil, os, re
from pathlib import Path


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ""


def run_scan() -> dict:
    checks, warnings = [], []

    # ── Disk ─────────────────────────────────────────────────────────
    for line in _run("df -h --output=target,pcent,avail 2>/dev/null").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            pct   = int(parts[1].replace("%", ""))
            mount = parts[0]
            avail = parts[2] if len(parts) > 2 else "?"
            icon  = "🟢" if pct < 70 else ("🟡" if pct < 85 else "🔴")
            checks.append({
                "label":       f"{icon} Disco {mount}",
                "description": f"{pct}% usado — {avail} livre",
                "command":     "fix disco cheio" if pct >= 85 else "",
            })
            if pct >= 85:
                warnings.append(f"Disco {mount} quase cheio ({pct}%)")
        except (ValueError, IndexError):
            pass

    # ── RAM ───────────────────────────────────────────────────────────
    for line in _run("free -m").splitlines():
        if line.startswith("Mem:"):
            parts   = line.split()
            total   = int(parts[1])
            used    = int(parts[2])
            avail   = int(parts[6]) if len(parts) > 6 else total - used
            pct     = int(used / total * 100) if total else 0
            icon    = "🟢" if pct < 70 else ("🟡" if pct < 85 else "🔴")
            checks.append({
                "label":       f"{icon} RAM",
                "description": f"{used}MB / {total}MB ({pct}%) — {avail}MB livre",
                "command":     "fix sistema lento" if pct >= 85 else "",
            })
            if pct >= 85:
                warnings.append("RAM crítica — considere encerrar processos pesados")
        if line.startswith("Swap:"):
            parts = line.split()
            if len(parts) >= 3 and parts[1].isdigit():
                total = int(parts[1])
                used  = int(parts[2]) if parts[2].isdigit() else 0
                if total > 0:
                    pct  = int(used / total * 100)
                    icon = "🟢" if pct < 50 else "🟡"
                    checks.append({
                        "label":       f"{icon} SWAP",
                        "description": f"{used}MB / {total}MB ({pct}%)",
                        "command":     "",
                    })

    # ── Load average ──────────────────────────────────────────────────
    m = re.search(r"load average[s]?:\s*([\d.]+)", _run("uptime"))
    if m:
        load  = float(m.group(1))
        cpus  = os.cpu_count() or 1
        ratio = load / cpus
        icon  = "🟢" if ratio < 0.7 else ("🟡" if ratio < 1.2 else "🔴")
        status = "Normal" if ratio < 0.7 else ("Elevada" if ratio < 1.2 else "Crítica")
        checks.append({
            "label":       f"{icon} Load CPU",
            "description": f"{load:.2f} (de {cpus} CPUs) — {status}",
            "command":     "fix sistema lento" if ratio >= 1.2 else "",
        })
        if ratio >= 1.2:
            warnings.append("Carga do sistema muito alta")

    # ── Failed services ───────────────────────────────────────────────
    failed = _run("systemctl list-units --failed --no-legend 2>/dev/null | head -5")
    if failed.strip():
        units = [l.split()[0] for l in failed.splitlines() if l.strip()]
        checks.append({
            "label":       f"🔴 Serviços com falha",
            "description": ", ".join(units),
            "command":     "fix serviço parado",
        })
        warnings.append(f"Serviços falhando: {', '.join(units)}")
    else:
        checks.append({
            "label":       "🟢 Serviços systemd",
            "description": "Nenhum serviço com falha",
            "command":     "",
        })

    # ── Last boot ─────────────────────────────────────────────────────
    boot = _run("uptime --since 2>/dev/null || who -b 2>/dev/null | awk '{print $3,$4}'")
    if boot:
        checks.append({
            "label":       "🔵 Último boot",
            "description": boot.strip(),
            "command":     "",
        })

    # ── Pending updates (apt) ─────────────────────────────────────────
    if shutil.which("apt"):
        raw_count = _run("apt list --upgradable 2>/dev/null | grep -vc 'Listing'") or "0"
        try:
            count = int(raw_count.strip())
            icon  = "🟢" if count == 0 else "🟡"
            checks.append({
                "label":       f"{icon} Atualizações",
                "description": f"{count} pacote(s) disponível(is)",
                "command":     "sudo apt upgrade" if count > 0 else "",
            })
            if count > 0:
                warnings.append(f"{count} pacotes têm atualização disponível")
        except ValueError:
            pass

    # ── Root warning ──────────────────────────────────────────────────
    if os.geteuid() == 0:
        warnings.append("Sessão como root — use um usuário normal sempre que possível")

    return {
        "type":    "scan",
        "title":   "Relatório de Saúde do Sistema",
        "body":    f"Análise executada em {_run('date')}",
        "steps":   checks,
        "warning": "\n".join(f"• {w}" for w in warnings) if warnings else "",
        "tip":     "Execute 'scan' regularmente para monitorar seu sistema.",
    }
