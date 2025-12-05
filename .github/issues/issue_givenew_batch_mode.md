# Issue #3: Batch režim pro givenew pomocí OpenAI Batch API

## Popis problému

Aktuální implementace `givephotobankreadymediafiles` (givenew) zpracovává fotky **interaktivně v reálném čase**:
- Otevře GUI okno pro každou fotku
- Čeká na AI odpověď pro každé jednotlivé pole (název, popis, klíčová slova, kategorie)
- Uživatel musí být přítomen a schvalovat metadata v reálném čase

### Nevýhody současného přístupu
- **Časově náročné**: Uživatel musí čekat na každou AI odpověď
- **Drahé**: Každá synchronní API request je dražší než batch
- **Neefektivní**: Nelze zpracovat velké množství fotek najednou
- **Nutná přítomnost**: Uživatel nemůže pustit skript a odejít

### Požadovaný Batch režim
- Uživatel **nejprve popíše všechny fotky** (batch) do textboxů
- Skript **odešle všechny popisy najednou** do OpenAI Batch API
- Skript může **počkat na výsledky** (s timeoutem) NEBO se ukončit a načíst výsledky při dalším spuštění
- **Stateful design**: Skript si pamatuje, co už bylo zpracováno, co čeká na odpověď, co už bylo odesláno

## Návrh UI

### Varianta A: Velký textbox pro volný popis

GUI okno obsahuje:
- Náhled fotky/videa
- **Velký textbox (250+ znaků)**: "Co nejpodrobněji popište, co je na obrázku/videu:"
- Tlačítka: "Uložit a pokračovat", "Přeskočit", "Ukončit"

**Výhody:**
- Jednoduchá implementace
- Flexibilní pro uživatele
- AI může extrahovat potřebné informace z volného textu

**Nevýhody:**
- Méně strukturované vstupy
- Uživatel musí znát, jaké informace jsou důležité

### Varianta B: Strukturované otázky podle pravidel fotobank

GUI okno obsahuje několik textboxů s konkrétními otázkami:

1. **Hlavní subjekt**: "Co je hlavní subjekt fotografie?" (povinné, 50+ znaků)
2. **Detailní popis**: "Popište detailně, co se děje na fotografii" (povinné, 100+ znaků)
3. **Umístění a kontext**: "Kde to je? Jaké je prostředí?" (50+ znaků)
4. **Emoce a atmosféra**: "Jakou emoce nebo atmosféru fotka evokuje?" (50+ znaků)
5. **Barvy a kompozice**: "Jaké jsou dominantní barvy a jak je kompozice?" (50+ znaků)
6. **Použití/účel**: "K čemu by se tato fotka dala použít?" (např. reklama, ilustrace, článek)

**Výhody:**
- Zajištění kompletních informací podle pravidel fotobank
- Strukturovanější vstupy pro AI
- Lepší kvalita výsledných metadat

**Nevýhody:**
- Složitější implementace
- Více času pro uživatele na vyplnění

### Pravidla fotobank pro metadata

#### Shutterstock (2025)
- **Popis**: Max 200 znaků, v angličtině
- **Kategorie**: 1 povinná, 2. volitelná
- **Klíčová slova**: Relevantní, bez trademark
- **Editorial**: Musí obsahovat CITY, STATE/COUNTRY – MONTH DAY, YEAR: faktický popis

#### Adobe Stock (2025)
- **Klíčová slova**: Max 49, prvních 10 je nejdůležitějších, v pořadí relevance
- **Překlad**: Automatický překlad do lokálních jazyků
- **Zákaz**: Jména umělců, skutečných osob, fiktivních postav v title/keywords

#### DreamsTime (2025)
- **Kategorie**: 3 kategorie (pro AI obsah: Illustrations & Clipart > AI-generated + 2 další)
- **Formát**: JPG, RGB, sRGB, 3-70 MP
- **AI metadata**: Automatická generace při uploadu (title, description, keywords, categories)

### Doporučení
**Použít Variantu A** (velký textbox) v první verzi:
- Rychlejší implementace
- Snazší pro uživatele
- AI modely (GPT-4o) jsou dostatečně pokročilé na extrakci strukturovaných dat z volného textu
- Varianta B může být přidána později jako "advanced mode"

## Architektura Batch režimu

### Přepínač pro aktivaci

```bash
# Standardní režim (aktuální)
python givephotobankreadymediafiles.py --batch_size 10

# Batch režim
python givephotobankreadymediafiles.py --batch_mode --batch_size 10 --batch_wait_timeout 3600
```

Parametry:
- `--batch_mode`: Aktivuje batch režim
- `--batch_size`: Počet fotek v jedné skupině (default: 10)
- `--batch_wait_timeout`: Timeout v sekundách pro čekání na Batch API odpověď (default: 3600 = 1 hodina, 0 = neomezeno)

### Stateful design

Skript musí udržovat stav v perzistentním úložišti (JSON soubor):

```json
{
  "batch_id": "batch_abc123",
  "created_at": "2025-10-24T10:30:00",
  "files": [
    {
      "file_path": "J:\\Foto\\IMG_1234.JPG",
      "hash": "sha256:abc123...",
      "status": "pending",
      "user_description": null,
      "batch_request_id": null,
      "custom_id": null,
      "result": null
    },
    {
      "file_path": "J:\\Foto\\IMG_1235.JPG",
      "hash": "sha256:def456...",
      "status": "description_saved",
      "user_description": "Krásný západ slunce nad horami, zlatá hodina...",
      "batch_request_id": null,
      "custom_id": "img_1235_abc123",
      "result": null
    },
    {
      "file_path": "J:\\Foto\\IMG_1236.JPG",
      "hash": "sha256:ghi789...",
      "status": "batch_sent",
      "user_description": "Portrét ženy v parku...",
      "batch_request_id": "req_xyz789",
      "custom_id": "img_1236_abc123",
      "result": null
    },
    {
      "file_path": "J:\\Foto\\IMG_1237.JPG",
      "hash": "sha256:jkl012...",
      "status": "batch_completed",
      "user_description": "Makro fotka květiny...",
      "batch_request_id": "req_xyz789",
      "custom_id": "img_1237_abc123",
      "result": {
        "title": "Beautiful sunset over mountains",
        "description": "...",
        "keywords": ["sunset", "mountains", "landscape", ...],
        "categories": {...}
      }
    },
    {
      "file_path": "J:\\Foto\\IMG_1238.JPG",
      "hash": "sha256:mno345...",
      "status": "saved_to_csv",
      "user_description": "...",
      "batch_request_id": "req_xyz789",
      "custom_id": "img_1238_abc123",
      "result": {...}
    }
  ]
}
```

### Stavy souborů

1. **`pending`**: Soubor byl vybrán, ale uživatel ještě nevyplnil popis
2. **`description_saved`**: Uživatel vyplnil popis a uložil ho
3. **`batch_sent`**: Soubor byl odeslán do Batch API (čeká na zpracování)
4. **`batch_completed`**: Batch API vrátil výsledek, metadata jsou připravena
5. **`saved_to_csv`**: Metadata byla uložena do PhotoMedia.csv
6. **`error`**: Chyba při zpracování

### Workflow

```
┌─────────────────────────────────────────────────────┐
│ 1. VÝBĚR SOUBORŮ                                    │
│    - Načti X souborů (batch_size) se statusem       │
│      "nezpracováno" z MediaCSV                      │
│    - Vytvoř nebo načti batch state JSON            │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 2. SBĚR POPISŮ OD UŽIVATELE                         │
│    FOR každý soubor:                                │
│      - Zkontroluj status v batch state              │
│      - Pokud pending → zobraz GUI s textboxem       │
│      - Uživatel vyplní popis (250+ znaků)           │
│      - Ulož popis do batch state                    │
│      - Změň status na "description_saved"           │
│      - GUI se zavře, další soubor po intervalu     │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 3. PŘÍPRAVA BATCH REQUESTU                          │
│    - Najdi všechny soubory se status               │
│      "description_saved"                            │
│    - Vytvoř JSONL soubor s requesty                │
│    - Každý request má custom_id = hash + index     │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 4. ODESLÁNÍ DO BATCH API                            │
│    - Odešli JSONL do OpenAI Batch API              │
│    - Získej batch_id                                │
│    - Ulož batch_id do batch state                   │
│    - Změň status souborů na "batch_sent"            │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 5. ČEKÁNÍ NA VÝSLEDKY (OPTIONAL)                   │
│    IF batch_wait_timeout > 0:                       │
│      - Poll Batch API každých 60 sekund            │
│      - Kontroluj status batch jobu                  │
│      - Timeout po batch_wait_timeout sekundách      │
│    ELSE:                                            │
│      - Ukončit skript (pokračovat příště)          │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 6. NAČTENÍ VÝSLEDKŮ                                 │
│    - Stáhni output JSONL z Batch API               │
│    - Parse JSONL, mapuj přes custom_id              │
│    - Ulož výsledky do batch state                   │
│    - Změň status na "batch_completed"               │
└────────────────┬────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────┐
│ 7. ULOŽENÍ DO MEDIACSV                              │
│    - Načti MediaCSV                                 │
│    - Pro každý soubor s "batch_completed":          │
│      - Najdi záznam v CSV                           │
│      - Aktualizuj metadata                          │
│      - Změň status na "připraveno"                  │
│    - Ulož CSV                                       │
│    - Změň status souborů na "saved_to_csv"          │
└─────────────────────────────────────────────────────┘
```

## Technická implementace

### 1. Batch State Manager

```python
# givephotobankreadymediafileslib/batch_state.py

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class BatchState:
    """Manager pro perzistentní stav batch zpracování."""

    def __init__(self, state_file: str = "./batch_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Načti existující stav nebo vytvoř nový."""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "batch_id": self._generate_batch_id(),
                "created_at": datetime.now().isoformat(),
                "files": []
            }

    def _generate_batch_id(self) -> str:
        """Generuj unikátní batch ID."""
        timestamp = datetime.now().isoformat()
        return f"batch_{hashlib.sha256(timestamp.encode()).hexdigest()[:8]}"

    def add_file(self, file_path: str) -> None:
        """Přidej soubor do batch state."""
        file_hash = self._compute_file_hash(file_path)
        custom_id = f"{Path(file_path).stem}_{self.state['batch_id']}"

        # Zkontroluj, zda soubor už není v seznamu
        if not any(f['file_path'] == file_path for f in self.state['files']):
            self.state['files'].append({
                "file_path": file_path,
                "hash": file_hash,
                "status": "pending",
                "user_description": None,
                "batch_request_id": None,
                "custom_id": custom_id,
                "result": None
            })
            self._save_state()

    def update_file_status(self, file_path: str, status: str, **kwargs) -> None:
        """Aktualizuj status souboru a další informace."""
        for file_info in self.state['files']:
            if file_info['file_path'] == file_path:
                file_info['status'] = status
                file_info.update(kwargs)
                break
        self._save_state()

    def get_files_by_status(self, status: str) -> List[Dict]:
        """Získej všechny soubory s daným statusem."""
        return [f for f in self.state['files'] if f['status'] == status]

    def _compute_file_hash(self, file_path: str) -> str:
        """Vypočítej SHA256 hash souboru."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"

    def _save_state(self) -> None:
        """Ulož stav do JSON souboru."""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
```

### 2. Batch API Client

```python
# givephotobankreadymediafileslib/batch_api.py

import json
import time
import base64
from pathlib import Path
from typing import List, Dict, Optional
import openai
from openai import OpenAI

class BatchAPIClient:
    """Client pro práci s OpenAI Batch API."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def create_batch_request(self, files_data: List[Dict], prompt_template: str) -> str:
        """
        Vytvoř JSONL soubor s batch requesty.

        Args:
            files_data: Seznam dict s file_path, custom_id, user_description
            prompt_template: Šablona promptu pro AI

        Returns:
            Cesta k vytvořenému JSONL souboru
        """
        jsonl_path = Path("./batch_requests.jsonl")

        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for file_data in files_data:
                # Načti obrázek jako base64
                with open(file_data['file_path'], 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')

                # Vytvoř prompt s uživatelským popisem
                prompt = prompt_template.format(
                    user_description=file_data['user_description']
                )

                # Vytvoř request
                request = {
                    "custom_id": file_data['custom_id'],
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 1000,
                        "response_format": {"type": "json_object"}
                    }
                }

                f.write(json.dumps(request) + '\n')

        return str(jsonl_path)

    def submit_batch(self, jsonl_file: str) -> str:
        """
        Odešli batch do OpenAI API.

        Returns:
            Batch ID
        """
        # Upload JSONL file
        with open(jsonl_file, 'rb') as f:
            batch_input_file = self.client.files.create(
                file=f,
                purpose="batch"
            )

        # Create batch
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        return batch.id

    def check_batch_status(self, batch_id: str) -> Dict:
        """Zkontroluj status batch jobu."""
        batch = self.client.batches.retrieve(batch_id)
        return {
            "status": batch.status,  # validating, in_progress, completed, failed, expired, cancelled
            "request_counts": batch.request_counts,
            "output_file_id": batch.output_file_id if hasattr(batch, 'output_file_id') else None
        }

    def retrieve_results(self, output_file_id: str) -> List[Dict]:
        """
        Stáhni a zparsuj výsledky z Batch API.

        Returns:
            Seznam výsledků s custom_id a response
        """
        file_response = self.client.files.content(output_file_id)
        results = []

        for line in file_response.text.strip().split('\n'):
            result = json.loads(line)
            results.append({
                "custom_id": result["custom_id"],
                "response": result["response"]["body"]["choices"][0]["message"]["content"]
            })

        return results

    def wait_for_completion(self, batch_id: str, timeout: int = 3600, poll_interval: int = 60) -> Dict:
        """
        Čekej na dokončení batch jobu s timeoutem.

        Args:
            batch_id: ID batch jobu
            timeout: Timeout v sekundách (0 = neomezeno)
            poll_interval: Interval kontroly v sekundách

        Returns:
            Status dict nebo None při timeoutu
        """
        start_time = time.time()

        while True:
            status = self.check_batch_status(batch_id)

            if status["status"] in ["completed", "failed", "expired", "cancelled"]:
                return status

            if timeout > 0 and (time.time() - start_time) > timeout:
                return None  # Timeout

            time.sleep(poll_interval)
```

### 3. Prompt pro Batch režim

```python
# givephotobankreadymediafileslib/prompts.py

BATCH_MODE_PROMPT = """
You are a professional stock photography metadata generator. Based on the image and the user's description, generate comprehensive metadata for stock photo platforms.

USER'S DESCRIPTION:
{user_description}

Generate the following metadata in JSON format:

{{
  "title": "A concise, descriptive title (max 70 characters)",
  "description": "A detailed description highlighting what, where, when, who, and the mood/atmosphere (max 200 characters)",
  "keywords": ["keyword1", "keyword2", ...],  // 30-49 relevant keywords in order of importance
  "categories": {{
    "shutterstock": ["Primary Category", "Secondary Category"],  // max 2
    "adobestock": ["Single Category"],  // exactly 1
    "dreamstime": ["Category 1", "Category 2", "Category 3"]  // exactly 3
  }}
}}

IMPORTANT RULES:
- All text must be in English
- Title: Concise, specific, searchable
- Description: Factual, no marketing language, describe actual content
- Keywords: Start with most relevant, no duplicates, lowercase
- Categories: Must match platform-specific category trees
- NO trademarks, brand names, or people names
- For editorial content, include location and date information

Analyze the image carefully and combine it with the user's description to generate accurate, commercially valuable metadata.
"""
```

### 4. Modifikace givephotobankreadymediafiles.py

Přidat logiku pro batch režim:

```python
# V parse_arguments():
parser.add_argument("--batch_mode", action="store_true",
                    help="Enable batch mode with OpenAI Batch API")
parser.add_argument("--batch_wait_timeout", type=int, default=3600,
                    help="Timeout in seconds to wait for batch completion (0 = no wait)")
parser.add_argument("--batch_state_file", type=str, default="./batch_state.json",
                    help="Path to batch state file")

# V main():
if args.batch_mode:
    # Batch workflow
    from givephotobankreadymediafileslib.batch_processor import BatchProcessor

    processor = BatchProcessor(
        media_csv=args.photo_csv,
        batch_size=args.batch_size,
        state_file=args.batch_state_file,
        wait_timeout=args.batch_wait_timeout
    )

    processor.run()
else:
    # Standardní interaktivní workflow (současný kód)
    ...
```

## Implementační kroky

- [ ] Prostudovat OpenAI Batch API dokumentaci (cookbook, API reference)
- [ ] Navrhnout strukturu batch state JSON
- [ ] Implementovat `BatchState` class (batch_state.py)
- [ ] Implementovat `BatchAPIClient` class (batch_api.py)
- [ ] Vytvořit prompt template pro batch režim (prompts.py)
- [ ] Vytvořit jednoduché GUI s velkým textboxem pro popis
- [ ] Implementovat `BatchProcessor` class (batch_processor.py):
  - [ ] Fáze 1: Sběr popisů od uživatele
  - [ ] Fáze 2: Vytvoření JSONL requestu
  - [ ] Fáze 3: Odeslání do Batch API
  - [ ] Fáze 4: Čekání na výsledky (s timeoutem)
  - [ ] Fáze 5: Načtení výsledků
  - [ ] Fáze 6: Uložení do MediaCSV
- [ ] Přidat CLI argumenty do givephotobankreadymediafiles.py
- [ ] Integrovat batch režim do main()
- [ ] Implementovat recovery při přerušení (načtení state, pokračování)
- [ ] Otestovat s malým batch (5 fotek)
- [ ] Otestovat s velkým batch (50 fotek)
- [ ] Otestovat timeout a obnovení
- [ ] Otestovat restart PC v průběhu (stateful recovery)
- [ ] Napsat unit testy
- [ ] Napsat integration testy
- [ ] Aktualizovat dokumentaci
- [ ] Porovnat náklady: standardní režim vs. batch režim

## Rozhodnutí k diskusi

### 1. Architektura podskriptu

**Možnost A**: Upravit stávající `preparemediafile.py`
- Přidat batch logiku do stávajícího skriptu
- Jednodušší údržba
- Větší složitost jednoho souboru

**Možnost B**: Vytvořit nový `preparemediafilebatch.py`
- Oddělená batch logika
- Čistší kód
- Duplicita některých částí

**Doporučení**: Možnost A - upravit `preparemediafile.py`, logiku rozdělit do modulů

### 2. UI: Varianta A vs. B

**Doporučení**: Začít s Variantou A (velký textbox), přidat Variantu B později jako `--batch_mode_advanced`

### 3. Čekání na výsledky

**Možnost A**: Vždy čekat (blokující)
**Možnost B**: Timeout parametr
**Možnost C**: Asynchronní + načtení příště

**Doporučení**: Možnost B - timeout parametr (default 1 hodina), možnost C jako budoucí vylepšení

## Odhad nákladů

### OpenAI Batch API Pricing (50% sleva oproti standardnímu API)

Standardní ceny:
- GPT-4o: $2.50 / 1M input tokens, $10.00 / 1M output tokens

Batch ceny:
- GPT-4o: $1.25 / 1M input tokens, $5.00 / 1M output tokens

Odhad pro 1 fotku:
- Input: ~1500 tokens (prompt + obrázek low-res + user description)
- Output: ~500 tokens (JSON metadata)
- Náklady: ~$0.004 per fotka v batch režimu
- Náklady: ~$0.008 per fotka ve standardním režimu

**Úspora: 50% + rychlejší zpracování velkých batch**

## Související soubory

- `givephotobankreadymediafiles/givephotobankreadymediafiles.py`
- `givephotobankreadymediafiles/preparemediafile.py`
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/batch_state.py` (NEW)
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/batch_api.py` (NEW)
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/batch_processor.py` (NEW)
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/prompts.py` (NEW)
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/media_viewer.py` (UI úpravy)

---

# AKTUALIZACE PO DŮKLADNÉ ANALÝZE

**Datum**: 2025-12-05
**Analytik**: Claude (Sonnet 4.5)
**Rozsah**: Identifikováno 42 kritických zádrhelů, všechny probrány a vyřešeny

## Shrnutí analýzy

Původní návrh batch režimu byl podroben důkladné analýze zaměřené na:
1. **Technické zádrhely** (P0, P1, P2) - limity API, konkurence, validace
2. **Procesní zádrhely** (P0-P1) - synchronizace stavů, konflikt batch↔manual režimů
3. **Uživatelské scénáře** - všechny možné edge cases a konfliktní situace

**Výsledek**: Všechny kritické problémy identifikovány a vyřešeny. Implementace **DOPORUČENA** s níže uvedenými rozhodnutími.

---

## KRITICKÁ ARCHITEKTONICKÁ ROZHODNUTÍ

### 1. Batch Size & Structure

**Problém**: OpenAI Batch API limit 100MB JSONL, base64 overhead 33%.

**Rozhodnutí**:
- **Vision batch size**: 20 fotek (default) kvůli 100MB limitu
- **Alternative batch size**: ~2000 souborů (text-only, bez vision)
- **Parametr `--batch_size`**: Celkový počet fotek v run → automaticky rozdělí na multiple OpenAI batches

**Příklad**:
```bash
python givephotobankreadymediafiles.py --batch_mode --batch_size 100
# Vytvoří:
# - 5× vision batch (20 fotek each) pro originals
# - 5× text-only batch (100 alternatives each) pro každý typ (_bw, _negative, atd.)
# CELKEM: 10 OpenAI batchů
```

### 2. Image Preprocessing Pipeline

**Problém**: Velké obrázky přesahují 100MB base64 limit.

**Rozhodnutí**:
- **Progressive resize**: Start 4000px @ quality 90%
- If still too large → resize to 3000px @ quality 90%
- Continue until fits nebo minimum 2000px
- **Minimum**: 2000px (pod tímto = skip)
- **Skip handling**: Status zůstane "nezpracováno" (možnost manual mode)
- **RAW handling**: On-the-fly convert to JPG pokud se nevejde

### 3. Workflow Architecture (3 fáze)

**KRITICKÉ**: Batch režim MUSÍ dodržet toto pořadí:

```
FÁZE 0: Cleanup (auto při startu)
└─ Delete completed batches > 12 měsíců

FÁZE 1: Retrieve Completed Batches
├─ Scan batch_registry.json pro batche se status="sent"
├─ Check každou na OpenAI API (parallel, progress bar)
├─ If status="completed" → retrieve results
├─ Save metadata to CSV (transactional - per file)
├─ Update status="batch_completed" v registry
└─ Mark failed files for retry

FÁZE 2: Send Ready Batches
├─ Check daily batch limit (OpenAI: 500/day)
├─ If limit reached → keep batches as "ready", try tomorrow
├─ Scan batch_registry.json pro batche se status="ready"
├─ Send každou (sequential, progress bar)
├─ Update status="sent" + store openai_batch_id
└─ Handle upload failures (error-specific: size→split, network→retry)

FÁZE 3: Collect New Descriptions (GUI loop)
├─ Find or create active "collecting" batch
├─ Load PhotoMedia.csv → filter status="nezpracováno"
├─ SKIP files in active batches (read batch_state)
├─ For each file:
│  ├─ Show GUI (textbox 50+ chars minimum, progress bar)
│  ├─ Editorial checkbox → modal dialog (same as regular mode)
│  ├─ Save/Reject/Show in Explorer buttons
│  ├─ Save description to batch_state
│  └─ If batch full (reaches --batch_size) → mark "ready", create new
└─ Generate alternatives metadata (text-only, separate batches)
```

**SEKVENČNÍ PROCESSING ALTERNATIVES**:
- Alternative step JEN až po completion stejného stepu na originals
- Např: FÁZE 1 retrieve originals → pak FÁZE 1 retrieve alternatives

### 4. Batch State Management

**Storage struktura**:
```
BATCH_STATE_DIR/
├── batch_registry.json          # Global index všech batchů + file registry
├── batches/
│   ├── batch_abc123/
│   │   ├── state.json           # Files, status, metadata
│   │   ├── descriptions.json    # User descriptions
│   │   └── results.json         # AI results po completion
│   └── batch_xyz789/
│       └── ...
```

**batch_registry.json** (klíčový soubor):
```json
{
  "active_batches": {
    "batch_abc123": {
      "status": "collecting|ready|sent|completed",
      "created_at": "2024-06-15T10:00:00",
      "batch_type": "originals|alternatives_bw|alternatives_negative|...",
      "file_count": 50,
      "batch_size_limit": 100,
      "openai_batch_id": null
    }
  },
  "completed_batches": [
    {"batch_id": "batch_old1", "completed_at": "2024-05-01T10:00:00"}
  ],
  "file_registry": {
    "J:\\Foto\\IMG_001.jpg": "batch_abc123"
  }
}
```

**Tracking**:
- **Global file registry**: Prevent duplicate files across batches (hard error)
- **Completed batches**: Skip already processed batches při resume
- **Daily batch count**: Track against OpenAI 500/day limit

### 5. Concurrency & Locking

**Problém**: Batch (stateful) vs. Manual (stateless) mode může způsobit data corruption.

**Rozhodnutí**:
- **Single instance only**: Hard lock file (msvcrt/fcntl)
- **Manual mode MUSÍ**: Číst batch_state → hard-skip soubory v active batchi
- **Lock violation**: Hard error + exit

**Manual mode filtrování**:
```python
def is_in_active_batch(file_path: str) -> bool:
    # Scan batch_registry.json
    for batch_id in active_batches:
        if file_path in batch_files[batch_id]:
            if status in ["collecting", "ready", "sent"]:
                return True
    return False

unprocessed = [f for f in records
               if f.status == "nezpracováno"
               and not is_in_active_batch(f.path)]
```

### 6. Alternatives Generation

**KRITICKÉ**: Batch režim BUDE generovat alternativy.

**Strategie**:
- **Separate batches** per alternative type (text-only, bez vision)
- **Batch structure**: Jedna batch = všechny pending soubory jednoho typu
  - `alternatives_bw`: až 2000 souborů
  - `alternatives_negative`: až 2000 souborů
  - atd.
- **Processing**: Sekvenční (originals completion → alternatives collection → alternatives send)
- **Prompt**: Totožné jako regular mode, AI dostane original metadata + alternative type

**Proces**:
```
1. FÁZE 1: Retrieve originals batches
2. FÁZE 1: Retrieve alternatives batches (až po 1.)
3. FÁZE 2: Send originals batches
4. FÁZE 2: Send alternatives batches (až po 3.)
5. FÁZE 3: Collect originals descriptions
6. FÁZE 3: Generate alternatives metadata → create alternative batches (až po 5.)
```

### 7. CSV Update Strategy

**Problém**: Transactional vs. all-or-nothing updates.

**Rozhodnutí**:
- **Transactional**: Save CSV after each file (minimize double-processing risk)
- **Backup**: Auto-backup při každém `save_csv_with_backup()` call (current behavior OK)
- **Status update**: Kopírovat regular mode logiku
  ```python
  # Update POUZE columns s "nezpracováno"
  for field_name, field_value in csv_record.items():
      if field_name.endswith(" status") and field_value == "nezpracováno":
          csv_record[field_name] = "připraveno"
  # SKIP columns které už mají "připraveno" nebo jiný status
  ```

### 8. Cost Calculation & Tracking

**Problém**: Issue odhad $0.004/fotka nezahrnuje vision tokens.

**Rozhodnutí**:
- **Přesný výpočet input tokens**:
  ```python
  prompt_tokens = tiktoken.encode(prompt_template)
  vision_tokens = calculate_vision_tokens(width, height, detail="high")
  description_tokens = tiktoken.encode(user_description)
  total_input = prompt_tokens + vision_tokens + description_tokens
  ```
- **Vision token formula** (OpenAI documented):
  ```python
  def calculate_vision_tokens(width, height, detail="high"):
      if detail == "low": return 85
      # Resize to fit 2048x2048, scale shortest to 768px
      # Count 512px tiles
      tiles_wide = (width + 511) // 512
      tiles_high = (height + 511) // 512
      return 85 + (tiles_wide * tiles_high * 170)
  ```
- **Output tokens**: Conservative estimate 150 tokens (actual varies)
- **Logging**: `cost_log.json` per batch:
  ```json
  {
    "batch_abc123": {
      "estimated_input_tokens": 65700,
      "estimated_output_tokens": 3000,
      "estimated_cost": 0.097,
      "actual_cost": null  // fill after completion
    }
  }
  ```
- **Display**: Show estimate před send, zobrazit breakdown na request

**Skutečný cost**:
```
Pro 4000×3000 obrázek:
- Prompt: 500 tokens
- Vision: 1785 tokens (high detail)
- Description: 100 tokens
- Output: 150 tokens (estimated)
= Input: 2385 tokens × $1.25/1M = $0.00298
= Output: 150 tokens × $5.00/1M = $0.00075
= TOTAL: $0.00373 per fotka (ne $0.004!)
```

---

## VŠECHNA TECHNICKÁ ROZHODNUTÍ

### P0 KRITICKÉ PROBLÉMY (Blockers)

#### #1: Base64 Limit Exceeded
**Rozhodnutí**: Progressive resize 4000px→2000px @ quality 90%, skip if still too large

#### #2: Concurrent Writes
**Rozhodnutí**: Single instance only, hard lock file, hard error on violation

#### #3: Custom ID Collisions
**Rozhodnutí**: Simple `{stem}_{batch_id}` (system garantuje unique filenames)

#### #4: CSV Update Strategy
**Rozhodnutí**: Transactional (save after each file to minimize double-processing)

#### #5: Orphaned Batches
**Rozhodnutí**: 3-fázový workflow, multi-batch registry, parallel retrieve

#### #6: File Hash Validation
**Rozhodnutí**: NE (user responsibility, re-validation by implementation)

### P1 ZÁVAŽNÉ PROBLÉMY

#### #7: Cost Calculation Error
**Rozhodnutí**: Přesný výpočet (tiktoken + vision formula), log to cost_log.json

#### #8: GUI Validation - Min Length
**Rozhodnutí**: Hard minimum 50 znaků, disable Save button

#### #9: Partial Recovery
**Rozhodnutí**: Auto-resume s preview info, MUSÍ pokračovat (bez volby cancel)

#### #10: Alternative Generation (řešeno výše)
**Rozhodnutí**: Separate text-only batches per type, ~2000 souborů per batch

#### #11: Batch Timeout
**Rozhodnutí**: Exit normálně při timeout, log info, pokračovat příště (podle issue návrhu)

#### #12: Failed Files in Batch
**Rozhodnutí**: Retry individually v sync mode (až 3 pokusy per file)

---

## PROCESNÍ ROZHODNUTÍ (State Management)

### #28: Batch ↔ Manual Mode Synchronization ⚠️ KRITICKÉ

**Problém**: Batch (stateful) vs. Manual (stateless) může způsobit data loss.

**Rozhodnutí**:
- Manual mode **MUSÍ** číst batch_state
- Hard-skip soubory které jsou v active batchi (status: collecting|ready|sent)
- Log: "Skipped 5 files (in active batch)"

### #29: Missing Files During Completion

**Rozhodnutí**: Mark as error v batch_state, continue with others
```json
{"file_path": "missing.jpg", "status": "file_not_found", "error": "..."}
```

### #30: Duplicate Files Across Batches

**Rozhodnutí**: Global file registry - prevent duplicates (hard error)
```python
if file in any_active_batch:
    raise Error(f"File {file} already in batch {batch_id}")
```

### #31: Resume After Interruption

**Rozhodnutí**: Již vyřešeno v #9 (auto-resume from last position)

### #32: Stale Batch State Detection

**Rozhodnutí**: Registry tracking completed batches → skip already processed

### #33: Alternatives Inconsistency

**Rozhodnutí**: Již vyřešeno v #10 (separate batches per type)

### #34: Mode Confusion

**Rozhodnutí**:
- Logging: `"=== BATCH MODE STARTED ==="`
- Progress bars pro všechny operace
- GUI title bar: `"[BATCH MODE] Collecting descriptions (50/100)"`

### #35: Upload Failure Handling

**Rozhodnutí**: Error-specific handling
```python
try:
    upload_batch(jsonl_file)
except FileSizeExceeded:
    split_batch_and_retry()
except NetworkTimeout:
    retry_with_backoff()
except RateLimitError:
    wait_and_retry()
except AuthenticationError:
    fail_permanently("Check API key")
# Implementor musí nastudovat OpenAI error types
```

### #36: Long-Running Batch

**Rozhodnutí**: Již vyřešeno v #11 (timeout + resume)

### #37: CSV Backup Timing

**Rozhodnutí**: Current behavior OK (transactional + auto-backup)

### #38: User Interruption (Ctrl+C)

**Rozhodnutí**: Immediate exit všude, batch state auto-saved after each operation (no special SIGINT handler needed)

### #39: Multi-Bank Status Update ⚠️ KRITICKÉ

**Rozhodnutí**: Kopírovat regular mode logiku
```python
# preparemediafile.py:156-160
for field_name, field_value in record.items():
    if field_name.endswith(" status") and field_value == "nezpracováno":
        record[field_name] = "připraveno"
# SKIP columns které už nejsou "nezpracováno"
```

### #40: Editorial Metadata ⚠️ KRITICKÉ

**Rozhodnutí**: Totožné jako regular mode
- Editorial checkbox v batch GUI
- Opens EditorialInfoDialog (modal)
- Save/Reject/Show in Explorer buttons fungují stejně

### #41: Cost Tracking

**Rozhodnutí**: Již vyřešeno v #7 (cost_log.json)

### #42: Batch Cleanup

**Rozhodnutí**: Auto-cleanup při startu, delete completed batches > 12 měsíců

---

## FINÁLNÍ ROZHODNUTÍ

### Daily Batch Limit (OpenAI: 500/day)

**Kalkulace**:
```
Jeden run (100 fotek):
- Originals: 5 vision batches (20 fotek each)
- Alternatives: 5 text-only batches (100 alternatives each)
= CELKEM: 10 OpenAI batches

500 limit / 10 = max 50 runs/day = 5,000 fotek/den
```

**Rozhodnutí**: Track daily count + graceful handling
```python
daily_count = get_todays_batch_count()  # Z OpenAI API
if daily_count + batch_count > 500:
    logging.warning("Daily limit would be exceeded")
    # Keep batch as "ready", send tomorrow
    break
```

### Notification System

**Rozhodnutí**: CLI check command
```bash
python givephotobankreadymediafiles.py --check-batch-status
# Output:
# Batch ABC123: completed (50 files ready)
# Batch XYZ789: in_progress (est. 2h remaining)
```

---

## GUI REQUIREMENTS

**Batch mode GUI MUSÍ být totožné s regular mode + additions**:

```
┌─────────────────────────────────────────────┐
│ [BATCH MODE] Give Photobank Ready Media... │ ← Title bar indicator
├─────────────────────────────────────────────┤
│                                             │
│  [Image Preview]                            │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ User Description (min 50 chars)     │   │
│  │                                     │   │
│  │ [Large textbox - 250+ chars]       │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [✓] Editorial → (opens modal)              │
│                                             │
│  [Save] [Reject] [Show in Explorer]        │
│                                             │
│  Progress: 50/100 files | Est: $0.50       │ ← Status bar
└─────────────────────────────────────────────┘
```

**Validace**:
- Save button disabled pokud `length < 50`
- Live character counter: "15/50 characters minimum"

---

## PROGRESS BARS (povinné)

```python
# FÁZE 1
for batch in tqdm(active_batches_sent, desc="Checking completed batches"):
    check_and_retrieve(batch)

# FÁZE 2
for batch in tqdm(ready_batches, desc="Sending batches to API"):
    send_batch(batch)

# FÁZE 3
for file in tqdm(unprocessed_files, desc="Collecting descriptions"):
    show_gui(file)

# Results processing
for file in tqdm(batch_results, desc="Saving metadata to CSV"):
    save_to_csv(file, metadata)
```

---

## IMPLEMENTAČNÍ DOPORUČENÍ

### Fázování

**Fáze 1 (MVP)**:
- ✅ Batch state management
- ✅ 3-fázový workflow
- ✅ GUI s textboxem
- ✅ Vision batches (originals only)
- ❌ Bez alternatives (přidat později)

**Fáze 2 (Full)**:
- ✅ Alternative generation
- ✅ Text-only batches
- ✅ Cost tracking
- ✅ Daily limit handling

### Testing Requirements

**KRITICKÉ test scenarios**:
1. **Batch↔Manual conflict**: Start batch → switch to manual → resume batch
2. **Interruption recovery**: Ctrl+C během každé fáze → resume
3. **Missing files**: Delete files během batch processing
4. **Duplicate detection**: Add same file to 2 batches
5. **API failures**: Network timeout, rate limit, size exceeded
6. **Cost calculation**: Verify vision token formula accuracy
7. **Multi-bank status**: Verify pouze "nezpracováno" columns updated

### P2 Issues (Implementor MUSÍ řešit)

Následující problémy jsou implementační detail, ale **NESMÍ být ignorovány**:

- **#16 Prompt injection**: Sanitize user descriptions (escape {}, newlines)
- **#17 Rate limits**: Již vyřešeno výše (daily limit tracking)
- **#18 JSON parsing**: Validate AI responses, handle malformed JSON
- **#19 Notifications**: Již vyřešeno výše (CLI check command)
- **#20 CSV encoding**: UTF-8-BOM consistency check
- **#21 Memory usage**: Stream large JSONL results (line-by-line parse)

---

## RIZIKA A MITIGACE

### Vysoké riziko

1. **Data corruption** (CSV conflicts)
   - Mitigace: Transactional updates + backups + lock file

2. **Cost overruns** (vision tokens)
   - Mitigace: Přesný výpočet + cost_log.json + display estimate

3. **State inconsistency** (batch vs. manual)
   - Mitigace: Manual mode read batch_state + hard-skip

4. **Lost work** (crashes, interruptions)
   - Mitigace: Auto-save after each operation + resume capability

### Střední riziko

5. **API rate limits** (500/day)
   - Mitigace: Daily count tracking + graceful queuing

6. **Missing files** (user moves/deletes)
   - Mitigace: Mark as error, continue with others

7. **Upload failures** (network, size)
   - Mitigace: Error-specific retry strategies

---

## ZÁVĚREČNÉ DOPORUČENÍ

**STATUS**: ✅ **GO - Implementace doporučena**

**Důvody**:
- ✅ Všechny blocking issues (P0) vyřešeny
- ✅ Všechny serious issues (P1) vyřešeny
- ✅ Všechny procesní konflikty vyřešeny
- ✅ Jasná architektura a rozhodnutí
- ✅ 50% cost benefit + bulk processing capability

**Podmínky**:
1. Implementátor **MUSÍ** číst všechna rozhodnutí v této sekci
2. **MUSÍ** implementovat všechna kritická rozhodnutí (P0, P1)
3. **MUSÍ** testovat všechny konfliktní scénáře (batch↔manual)
4. **DOPORUČENO** fázovat implementaci (MVP bez alternatives → Full s alternatives)

**Odhadovaná složitost**: 2-3× více než původní issue návrh (kvůli state synchronization a error handling)

**Benefit**: 50% cost savings + 10-50× faster bulk processing

---

**Konec aktualizace**