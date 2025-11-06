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