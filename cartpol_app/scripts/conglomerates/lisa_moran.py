"""
Local/Global Moran's I (LISA, Anselin 1995) implementado com numpy puro, sobre o
grafo de vizinhança de bairros já usado pelos conglomerados (contiguidade
'touches', simétrico). Sem dependência de pysal/esda.

Convenções:
- Pesos row-standardized: lag_i = média dos z dos vizinhos de i.
- I_local_i = (z_i / m2) * lag_i, com m2 = Σz²/N.
- I_global = Σ_i z_i·lag_i / Σ_i z_i²  (equivale à forma padrão com W row-std).
- Inferência por permutação condicional (Anselin 1995), RNG semeado.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def build_index(neighbors: Dict[str, List[str]]) -> Tuple[List[str], List[np.ndarray]]:
    """Universo = todos os bairros do grafo. Retorna (bairros, vizinhos_por_indice)."""
    bairros = sorted(neighbors.keys())
    idx = {b: i for i, b in enumerate(bairros)}
    nb_idx = [
        np.array([idx[n] for n in neighbors.get(b, []) if n in idx], dtype=int)
        for b in bairros
    ]
    return bairros, nb_idx


def _lag(z: np.ndarray, nb_idx: List[np.ndarray]) -> np.ndarray:
    """Média dos z dos vizinhos (row-standardized); 0 para bairro sem vizinhos."""
    lag = np.zeros(len(z))
    for i, nb in enumerate(nb_idx):
        if len(nb):
            lag[i] = z[nb].mean()
    return lag


def local_moran(x: np.ndarray, nb_idx: List[np.ndarray]):
    """Retorna (I_local, z, lag)."""
    z = x - x.mean()
    m2 = (z ** 2).sum() / len(z)
    lag = _lag(z, nb_idx)
    with np.errstate(divide="ignore", invalid="ignore"):
        I = (z / m2) * lag if m2 > 0 else np.zeros_like(z)
    return I, z, lag


def quadrant(z: np.ndarray, lag: np.ndarray) -> List[str]:
    """HH: alto entre altos; LL: baixo entre baixos; HL: outlier alto; LH: outlier baixo."""
    out = []
    for zi, li in zip(z, lag):
        if zi > 0 and li > 0:
            out.append("HH")
        elif zi > 0 and li <= 0:
            out.append("HL")
        elif zi <= 0 and li > 0:
            out.append("LH")
        else:
            out.append("LL")
    return out


def permutation_pvalues(x: np.ndarray, nb_idx: List[np.ndarray],
                        M: int = 999, seed: int = 42) -> np.ndarray:
    """Pseudo p-valores por permutação condicional: fixa x_i, sorteia os valores
    dos vizinhos dentre os demais N-1. p = (#{|I_perm| >= |I_obs|} + 1) / (M + 1)."""
    rng = np.random.default_rng(seed)
    N = len(x)
    z = x - x.mean()
    m2 = (z ** 2).sum() / N
    if m2 == 0:
        return np.ones(N)
    I_obs, _, _ = local_moran(x, nb_idx)
    pvals = np.ones(N)
    for i in range(N):
        k = len(nb_idx[i])
        if k == 0:
            continue
        others = np.delete(z, i)
        # M sorteios de k vizinhos (índices em others)
        draws = rng.integers(0, len(others), size=(M, k))
        lags = others[draws].mean(axis=1)
        I_perm = (z[i] / m2) * lags
        exceed = np.sum(np.abs(I_perm) >= abs(I_obs[i]))
        pvals[i] = (exceed + 1) / (M + 1)
    return pvals


def global_moran(x: np.ndarray, nb_idx: List[np.ndarray],
                 M: int = 999, seed: int = 42) -> Tuple[float, float]:
    """Moran global (W row-std) + pseudo p-valor por permutação total do vetor."""
    z = x - x.mean()
    ssz = (z ** 2).sum()
    if ssz == 0:
        return 0.0, 1.0
    lag = _lag(z, nb_idx)
    I_obs = float((z * lag).sum() / ssz)

    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(M):
        zp = rng.permutation(z)
        lp = _lag(zp, nb_idx)
        I_p = (zp * lp).sum() / ssz
        if abs(I_p) >= abs(I_obs):
            exceed += 1
    return I_obs, (exceed + 1) / (M + 1)


def largest_hh_cluster(bairros: List[str], quad: List[str], sig: np.ndarray,
                       neighbors: Dict[str, List[str]]) -> List[str]:
    """Maior componente conexo de bairros HH significativos (p<=0.05)."""
    hh = {b for b, q, s in zip(bairros, quad, sig) if q == "HH" and s}
    best: set = set()
    visited: set = set()
    for start in hh:
        if start in visited:
            continue
        comp, stack = set(), [start]
        while stack:
            b = stack.pop()
            if b in comp:
                continue
            comp.add(b)
            visited.add(b)
            stack.extend(n for n in neighbors.get(b, []) if n in hh and n not in comp)
        if len(comp) > len(best):
            best = comp
    return sorted(best)


def lisa_summary(votes_dict: Dict[str, int], neighbors: Dict[str, List[str]],
                 top_bairro: str, alpha: float = 0.05,
                 M: int = 999, seed: int = 42) -> Dict:
    """Resumo LISA para um candidato: Moran global+p, quadrantes/p locais,
    classe do bairro-reduto, contagens significativas e maior cluster HH."""
    bairros, nb_idx = build_index(neighbors)
    x = np.array([float(votes_dict.get(b, 0)) for b in bairros])

    I_local, z, lag = local_moran(x, nb_idx)
    quad = quadrant(z, lag)
    pvals = permutation_pvalues(x, nb_idx, M=M, seed=seed)
    sig = pvals <= alpha
    Ig, pg = global_moran(x, nb_idx, M=M, seed=seed)

    by_bairro = {
        b: {"I": round(float(I_local[i]), 4), "quad": quad[i],
            "p": round(float(pvals[i]), 4), "sig": bool(sig[i]),
            "votos": int(votes_dict.get(b, 0))}
        for i, b in enumerate(bairros)
    }
    top_info = by_bairro.get(top_bairro, {})
    return {
        "moran_global": round(Ig, 4),
        "moran_global_p": round(pg, 4),
        "n_sig": int(sig.sum()),
        "n_HH_sig": sum(1 for i in range(len(bairros)) if quad[i] == "HH" and sig[i]),
        "n_HL_sig": sum(1 for i in range(len(bairros)) if quad[i] == "HL" and sig[i]),
        "n_LH_sig": sum(1 for i in range(len(bairros)) if quad[i] == "LH" and sig[i]),
        "n_LL_sig": sum(1 for i in range(len(bairros)) if quad[i] == "LL" and sig[i]),
        "reduto": top_bairro,
        "reduto_quad": top_info.get("quad"),
        "reduto_p": top_info.get("p"),
        "reduto_sig": top_info.get("sig"),
        "maior_cluster_HH": largest_hh_cluster(bairros, quad, sig, neighbors),
        "by_bairro": by_bairro,
    }
