# Issue #4: Rozšíření přečíslování souborů z PICT na NIK_

## Popis problému

Skripty `pullnewmediatounsorted` a `removealreadysortedout` aktuálně volají funkci **`normalize_indexed_filenames()`** s parametrem `prefix="PICT"` pro přečíslování souborů z fotopasti Bunaty Micro 4K.

Tato funkce:
- Normalizuje číslování souborů s daným prefixem (např. PICT0195.JPG)
- Zajišťuje konzistentní sekvenční číslování
- Řeší duplicity podle hash
- Přiřazuje nejnižší dostupná čísla

## Požadavek

Rozšířit přečíslování na soubory s prefixem **NIK_** (z Nikon fotoaparátů) pomocí druhého volání stejné funkce s jiným prefixem.

### Příklad

**Aktuálně se zpracovává:**
```python
normalize_indexed_filenames(
    source_folder=args.target,
    reference_folder=args.final_target,
    prefix="PICT",  # Pouze PICT
    width=args.index_width,
    max_number=args.index_max,
)
```

**Požadovaný stav:**
```python
# Přečíslovat PICT soubory
normalize_indexed_filenames(
    source_folder=args.target,
    reference_folder=args.final_target,
    prefix="PICT",
    width=args.index_width,
    max_number=args.index_max,
)

# Přečíslovat NIK_ soubory (nové volání)
normalize_indexed_filenames(
    source_folder=args.target,
    reference_folder=args.final_target,
    prefix="NIK_",
    width=args.index_width,
    max_number=args.index_max,
)
```

## Umístění funkce

Funkce `normalize_indexed_filenames` je definována v:

1. **`pullnewmediatounsorted/pullnewmediatounsortedlib/renaming.py`** (řádky 39-45)
   ```python
   def normalize_indexed_filenames(
       source_folder: str,
       reference_folder: str,
       prefix: str = "PICT",
       width: int = DEFAULT_NUMBER_WIDTH,
       max_number: int = MAX_NUMBER
   ) -> None:
   ```

2. **`removealreadysortedout/removealreadysortedoutlib/renaming.py`** (řádky 39-45)
   - Identická implementace

## Místa volání

### 1. pullnewmediatounsorted.py

**Řádky 84-90:** Normalizace mezi target a final_target
```python
# 2) Normalize indexed filenames in target vs final_target
normalize_indexed_filenames(
    source_folder=args.target,
    reference_folder=args.final_target,
    prefix=args.index_prefix,
    width=args.index_width,
    max_number=args.index_max,
)
```

**➡️ PŘIDAT ZDE druhé volání s `prefix="NIK_"`**

**Řádky 94-100:** Normalizace mezi sources a target (v cyklu)
```python
# 3) Normalize indexed filenames in sources vs target
for folder in sources + screen_sources:
    normalize_indexed_filenames(
        source_folder=folder,
        reference_folder=args.target,
        prefix=args.index_prefix,
        width=args.index_width,
        max_number=args.index_max,
    )
```

**➡️ PŘIDAT UVNITŘ CYKLU druhé volání s `prefix="NIK_"`**

### 2. remove_already_sorted_out.py

**Řádky 79-85:** Normalizace mezi unsorted a target
```python
# Step 3: Normalize indexed filenames in unsorted vs target
logging.info("Step 3: Normalizing indexed filenames...")
normalize_indexed_filenames(
    source_folder=args.unsorted_folder,
    reference_folder=args.target_folder,
    prefix=args.index_prefix,
    width=args.index_width,
    max_number=args.index_max,
)
```

**➡️ PŘIDAT ZDE druhé volání s `prefix="NIK_"`**

## Implementační kroky

### Krok 1: pullnewmediatounsorted.py

- [x] Otevřít `pullnewmediatounsorted/pullnewmediatounsorted.py`
- [x] Přidána konstanta `PREFIXES_TO_NORMALIZE = ["PICT", "NIK_"]` do constants.py
- [x] Změněna implementace na iteraci přes `PREFIXES_TO_NORMALIZE` místo jednoho volání
- [x] První volání (řádek 86-93) nyní iteruje přes všechny prefixy
- [x] Druhé volání (řádek 97-104) nyní iteruje přes všechny prefixy v nested loop

### Krok 2: remove_already_sorted_out.py

- [x] Otevřít `removealreadysortedout/remove_already_sorted_out.py`
- [x] Přidána konstanta `PREFIXES_TO_NORMALIZE = ["PICT", "NIK_"]` do constants.py
- [x] Změněna implementace na iteraci přes `PREFIXES_TO_NORMALIZE` (řádek 80-87)
- [x] Normalizace nyní zpracovává všechny prefixy z konstanty

### Krok 3: Testování

- [ ] Vytvořit testovací složku s PICT a NIK_ soubory:
  - `PICT0001.JPG`, `PICT0005.JPG`, `PICT0010.JPG`
  - `NIK_0001.JPG`, `NIK_0003.JPG`, `NIK_0007.JPG`
- [ ] Spustit `pullnewmediatounsorted.py` a ověřit:
  - PICT soubory jsou přečíslovány (PICT0001, PICT0002, PICT0003)
  - NIK_ soubory jsou přečíslovány (NIK_0001, NIK_0002, NIK_0003)
  - Oba prefixy jsou přečíslovány **nezávisle**
- [ ] Spustit `remove_already_sorted_out.py` a ověřit stejné chování
- [ ] Otestovat s prázdnou složkou (bez PICT/NIK_ souborů)
- [ ] Otestovat s pouze PICT soubory (NIK_ by se mělo přeskočit)
- [ ] Otestovat s pouze NIK_ soubory (PICT by se mělo přeskočit)
- [ ] Zkontrolovat logy - měly by obsahovat info o obou prefixech

### Krok 4: Dokumentace

- [ ] Přidat komentáře do kódu vysvětlující, proč se volá dvakrát
- [ ] Aktualizovat README (pokud existuje) s informací o NIK_ podpoře
- [ ] Přidat do CLAUDE.md poznámku o podporovaných prefixech

## Poznámky

### Jak funkce funguje

Z `renaming.py` (řádky 47-49):
```python
"""
Upraví názvy souborů s daným `prefix` a číselným suffixem v `source_folder`:
  - Shodné obsahy podle hashů přejmenuje na stávající jméno z `reference_folder`.
  - Jiné přejmenuje na nejnižší dostupné číslo se zadanou `width`.
Renaming proběhne přímo na místě (změní se jen název, ne cesta ke složce).
"""
```

### Early exit při absenci souborů

Funkce má early check (řádky 57-61):
```python
# 1) Early check: skip if no files with prefix in source folder
paths = list_files(source_folder, pattern=prefix, recursive=True)
if not paths:
    logging.info("No files matching '%s*' in %s, skipping.", prefix, source_folder)
    return
```

**To znamená, že pokud nejsou žádné NIK_ soubory, funkce se automaticky přeskočí** - není potřeba žádná podmínka před voláním!

### Nezávislé číslování

PICT a NIK_ mají **samostatné číselné řady**:
- PICT0001, PICT0002, PICT0003
- NIK_0001, NIK_0002, NIK_0003

Nebudou se míchat:
- ❌ PICT0001, NIK_0002, PICT0003
- ✅ PICT0001, PICT0002, PICT0003 + NIK_0001, NIK_0002, NIK_0003

### Výkon

Druhé volání přidá overhead pouze pokud jsou NIK_ soubory přítomny. Pokud ne, funkce se okamžitě vrátí (early exit).

## Budoucí rozšíření

Pokud bude potřeba v budoucnu přidat další prefixy (např. "DJI_", "IMG_"), stačí přidat další volání:

```python
PREFIXES_TO_NORMALIZE = ["PICT", "NIK_", "DJI_", "IMG_"]

for prefix in PREFIXES_TO_NORMALIZE:
    normalize_indexed_filenames(
        source_folder=args.target,
        reference_folder=args.final_target,
        prefix=prefix,
        width=args.index_width,
        max_number=args.index_max,
    )
```

Toto lze implementovat v budoucí refaktoraci, ale pro Issue #4 stačí přidat pouze NIK_.

## Související soubory

- `pullnewmediatounsorted/pullnewmediatounsorted.py` (řádky 84-90, 94-100)
- `pullnewmediatounsorted/pullnewmediatounsortedlib/renaming.py` (definice funkce)
- `removealreadysortedout/remove_already_sorted_out.py` (řádky 79-85)
- `removealreadysortedout/removealreadysortedoutlib/renaming.py` (definice funkce)

## Odhad času

- Implementace: 15 minut
- Testování: 30 minut
- Celkem: ~45 minut

Jedná se o velmi jednoduchou změnu - pouze přidání několika řádků kódu na 3 místech.