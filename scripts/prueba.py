#!/usr/bin/env python3
"""
powerball_cooccurrence_2025.py
Descarga los resultados de Powerball 2025 desde powerball.net (o powerball.com si prefieres),
extrae los números blancos y calcula co-ocurrencias: para cada número 1..69 muestra con qué otros
números ha aparecido más veces en la misma jugada durante 2025.

Uso:
    python powerball_cooccurrence_2025.py
"""

import requests
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import re

import random
from collections import Counter, defaultdict

# ---- CONFIG ----
# URL del archivo de 2025 (puedes cambiar por powerball.com/previous-results si prefieres)
ARCHIVE_URL = "https://www.powerball.net/archive/2025"  # buena fuente con todo 2025
#ARCHIVE_URL = "https://www.powerball.com/previous-results"  # alternativa (puede requerir paginación)

# Cuántos co-ocurrentes mostrar por número
TOP_N = 6

# ---- funciones ----
def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text

def parse_archive_page(html):
    """
    Busca en la página todas las secuencias de números de Powerball.
    Espera líneas/elementos con formato tipo: 'September 22, 2025 3 29 42 46 59 15 ...'
    Devuelve lista de draws, cada draw = lista de 5 enteros (white balls).
    """
    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(" ", strip=True)
    # patrón heurístico: fecha (palabra) dígitos consecutivos -> capturar secuencia de 5 blancos + powerball
    # ejemplo: "September 22, 2025 3 29 42 46 59 15"
    pattern = re.compile(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*2025\s+((?:\d{1,2}\s+){5})\d{1,2}")
    matches = pattern.findall(text)

    draws = []
    for m in matches:
        nums = [int(x) for x in m.split() if x.strip()]
        if len(nums) == 5:
            draws.append(nums)
    return draws

def compute_cooccurrence(draws):
    # co[n] será Counter de otros números que salieron con n
    co = {n: Counter() for n in range(1,70)}
    for draw in draws:
        for a in draw:
            for b in draw:
                if a == b: continue
                co[a][b] += 1
    return co

def top_pairs_global(co):
    # sacar parejas (a,b) con a<b y contar cuantas veces ocurrieron
    pair_counts = Counter()
    for a in co:
        for b,count in co[a].items():
            if a < b:
                pair_counts[(a,b)] = count
    return pair_counts.most_common(30)

def main():
    print("Fetching archive page:", ARCHIVE_URL)
    html = fetch_page(ARCHIVE_URL)
    print("Parsing draws for 2025...")
    draws = parse_archive_page(html)
    print("Found draws:", len(draws))
    if len(draws) == 0:
        print("No se detectaron jugadas con el parser heurístico. Intenta usar powerball.com o revisar estructura HTML.")
        return

    co = compute_cooccurrence(draws)

    print("\nTop co-occurrent numbers por número (top {}):".format(TOP_N))
    for n in range(1,70):
        total = sum(co[n].values())
        if total == 0:
            continue
        top = co[n].most_common(TOP_N)
        top_str = ", ".join([f"{k}({v})" for k,v in top])
        pct = [f"{100*v/total:.1f}%" for _,v in top]
        print(f"{n:2d}: {top_str}  (total co-occ: {total})")

    print("\nParejas globales más frecuentes (top 20):")
    for (a,b),c in top_pairs_global(co)[:20]:
        print(f"{a}-{b}: {c} veces")

#!/usr/bin/env python3
"""
powerball_cooccurrence_2025.py
Descarga los resultados de Powerball 2025 desde powerball.net (o powerball.com si prefieres),
extrae los números blancos y calcula co-ocurrencias: para cada número 1..69 muestra con qué otros
números ha aparecido más veces en la misma jugada durante 2025.

Uso:
    python powerball_cooccurrence_2025.py
"""

import requests
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import re

# ---- CONFIG ----
# URL del archivo de 2025 (puedes cambiar por powerball.com/previous-results si prefieres)
ARCHIVE_URL = "https://www.powerball.net/archive/2025"  # buena fuente con todo 2025
#ARCHIVE_URL = "https://www.powerball.com/previous-results"  # alternativa (puede requerir paginación)

# Cuántos co-ocurrentes mostrar por número
TOP_N = 6

# ---- funciones ----
def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text

def parse_archive_page(html):
    """
    Busca en la página todas las secuencias de números de Powerball.
    Espera líneas/elementos con formato tipo: 'September 22, 2025 3 29 42 46 59 15 ...'
    Devuelve lista de draws, cada draw = lista de 5 enteros (white balls).
    """
    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(" ", strip=True)
    # patrón heurístico: fecha (palabra) dígitos consecutivos -> capturar secuencia de 5 blancos + powerball
    # ejemplo: "September 22, 2025 3 29 42 46 59 15"
    pattern = re.compile(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*2025\s+((?:\d{1,2}\s+){5})\d{1,2}")
    matches = pattern.findall(text)

    draws = []
    for m in matches:
        nums = [int(x) for x in m.split() if x.strip()]
        if len(nums) == 5:
            draws.append(nums)
    return draws

def compute_cooccurrence(draws):
    # co[n] será Counter de otros números que salieron con n
    co = {n: Counter() for n in range(1,70)}
    for draw in draws:
        for a in draw:
            for b in draw:
                if a == b: continue
                co[a][b] += 1
    return co

def top_pairs_global(co):
    # sacar parejas (a,b) con a<b y contar cuantas veces ocurrieron
    pair_counts = Counter()
    for a in co:
        for b,count in co[a].items():
            if a < b:
                pair_counts[(a,b)] = count
    return pair_counts.most_common(30)

def main():
    print("Fetching archive page:", ARCHIVE_URL)
    html = fetch_page(ARCHIVE_URL)
    print("Parsing draws for 2025...")
    draws = parse_archive_page(html)
    print("Found draws:", len(draws))
    if len(draws) == 0:
        print("No se detectaron jugadas con el parser heurístico. Intenta usar powerball.com o revisar estructura HTML.")
        return

    co = compute_cooccurrence(draws)

    print("\nTop co-occurrent numbers por número (top {}):".format(TOP_N))
    for n in range(1,70):
        total = sum(co[n].values())
        if total == 0:
            continue
        top = co[n].most_common(TOP_N)
        top_str = ", ".join([f"{k}({v})" for k,v in top])
        pct = [f"{100*v/total:.1f}%" for _,v in top]
        print(f"{n:2d}: {top_str}  (total co-occ: {total})")

    print("\nParejas globales más frecuentes (top 20):")
    for (a,b),c in top_pairs_global(co)[:20]:
        print(f"{a}-{b}: {c} veces")


# Ejemplo de datos (resultados históricos del 2025 hasta ahora).
# Cada jugada es una lista de 5 números + el Powerball (último).
resultados = [
    [1, 12, 18, 23, 45, 14],
    [7, 12, 23, 34, 56, 18],
    [12, 18, 23, 35, 42, 9],
    [1, 23, 35, 44, 62, 12],
    [12, 19, 23, 36, 48, 5],
    [18, 23, 34, 51, 62, 14],
    # ... aquí meteríamos todos los sorteos reales del 2025
]

def analizar_frecuencias(resultados):
    """Cuenta cuántas veces ha salido cada número (sin el Powerball)."""
    todos = [num for jugada in resultados for num in jugada[:-1]]  # sin incluir el Powerball
    return Counter(todos)

def analizar_coocurrencias(resultados):
    """Cuenta con qué números suele salir cada número."""
    coocurrencias = defaultdict(Counter)
    for jugada in resultados:
        for num in jugada[:-1]:
            for otro in jugada[:-1]:
                if num != otro:
                    coocurrencias[num][otro] += 1
    return coocurrencias

def generar_jugadas(frecuencias, coocurrencias, n=6):
    """Genera jugadas basadas en los números más frecuentes y sus coocurrencias."""
    jugadas = []
    top_nums = [num for num, _ in frecuencias.most_common(15)]  # top 15 más frecuentes
    
    for _ in range(n):
        base = random.sample(top_nums, 2)  # elijo 2 números base del top
        sugeridos = []
        for b in base:
            comunes = [n for n, _ in coocurrencias[b].most_common(3)]  # 3 más frecuentes con b
            sugeridos.extend(comunes)
        
        jugada = list(set(base + sugeridos))[:5]  # máximo 5 números
        while len(jugada) < 5:  # si falta, rellenar aleatorio
            extra = random.choice(top_nums)
            if extra not in jugada:
                jugada.append(extra)
        jugada.sort()
        powerball = random.randint(1, 26)  # Powerball al azar
        jugadas.append(jugada + [powerball])
    return jugadas


# ====== Ejecutar análisis ======
frecuencias = analizar_frecuencias(resultados)
coocurrencias = analizar_coocurrencias(resultados)
jugadas_sugeridas = generar_jugadas(frecuencias, coocurrencias)

print("📊 Jugadas sugeridas:")
for j in jugadas_sugeridas:
    print(j)




