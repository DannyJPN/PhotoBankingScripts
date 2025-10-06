from typing import Dict, List, Any, Callable, Optional, Union

# Typ pro transformační funkci
TransformFunc = Callable[[str], str]

# Typ pro definici sloupce
ColumnDef = Dict[str, Union[str, TransformFunc]]

# Typ pro mapu sloupců pro jednu banku
BankColumnMap = List[ColumnDef]

# Transformační funkce
def editorial_to_numeric(val: str) -> str:
    """Převede 'yes'/'no' na '1'/'0'"""
    return "1" if val == "yes" else "0"

def get_super_tags(val: str) -> str:
    """Získá prvních 10 klíčových slov jako super tagy"""
    return ",".join(val.split(",")[:10]) if val else ""

def check_people(val: str) -> str:
    """Zkontroluje, zda jsou na obrázku lidé"""
    return "crowd" if "people" in val.lower() or "crowd" in val.lower() else "0"

def check_property(val: str) -> str:
    """Zkontroluje, zda je na obrázku nemovitost"""
    return "Y" if "house" in val.lower() or "building" in val.lower() else "N"

def license_type_from_editorial(val: str) -> str:
    """Určí typ licence na základě editorial příznaku"""
    return "RF-E" if val == "yes" else "RF"

# Hlavní mapa sloupců pro všechny banky
BANK_COLUMN_MAPS: Dict[str, BankColumnMap] = {
    "ShutterStock": [
        {"target": "Filename", "source": "filename"},
        {"target": "Description", "source": "description"},
        {"target": "Keywords", "source": "keywords"},
        {"target": "Categories", "source": "shutterstock_cats"},
        {"target": "Editorial", "source": "editorial"},
        {"target": "Mature content", "source": "mature"},
        {"target": "illustration", "source": "vector"},
    ],

    "AdobeStock": [
        {"target": "Filename", "source": "filename"},
        {"target": "Title", "source": "description"},
        {"target": "Keywords", "source": "keywords"},
        {"target": "Category", "source": "adobe_cat_id"},
        {"target": "Releases", "value": ""},
    ],

    "DreamsTime": [
        {"target": "Filename", "source": "filename"},
        {"target": "Image Name", "source": "title"},
        {"target": "Description", "source": "description"},
        {"target": "Category 1", "source": "dreamstime_cat1"},
        {"target": "Category 2", "source": "dreamstime_cat2"},
        {"target": "Category 3", "source": "dreamstime_cat3"},
        {"target": "keywords", "source": "keywords"},
        {"target": "Free", "value": "0"},
        {"target": "W-EL", "value": "1"},
        {"target": "P-EL", "value": "1"},
        {"target": "SR-EL", "value": "0"},
        {"target": "SR-Price", "value": "0"},
        {"target": "Editorial", "source": "editorial", "transform": editorial_to_numeric},
        {"target": "MR doc Ids", "value": "0"},
        {"target": "Pr Docs", "value": "0"},
    ],

    "DepositPhotos": [
        {"target": "Filename", "source": "filename"},
        {"target": "description", "source": "description"},
        {"target": "Keywords", "source": "keywords"},
        {"target": "Nudity", "source": "nudity"},
        {"target": "Editorial", "source": "editorial"},
    ],

    "BigStockPhoto": [
        {"target": "filename", "source": "filename"},
        {"target": "description", "source": "description"},
        {"target": "keywords", "source": "keywords"},
        {"target": "categories", "source": "bigstock_cat"},
        {"target": "illustration", "source": "vector"},
        {"target": "editorial", "source": "editorial"},
    ],

    "123RF": [
        {"target": "oldfilename", "source": "filename"},
        {"target": "123rf_filename", "value": ""},
        {"target": "description", "source": "description"},
        {"target": "keywords", "source": "keywords"},
        {"target": "country", "source": "country"},
        {"target": "categories", "source": "rf123_cat"},
    ],

    "CanStockPhoto": [
        {"target": "filename", "source": "filename"},
        {"target": "title", "source": "title"},
        {"target": "description", "source": "description"},
        {"target": "keywords", "source": "keywords"},
        {"target": "categories", "source": "canstock_cat"},
    ],

    "Pond5": [
        {"target": "originalfilename", "source": "filename"},
        {"target": "title", "source": "title"},
        {"target": "description", "source": "description"},
        {"target": "keywords", "source": "keywords"},
        {"target": "location", "source": "location"},
        {"target": "specifysource", "value": ""},
        {"target": "copyright", "source": "copyright"},
        {"target": "price", "value": "5"},
        {"target": "imagetype", "value": "photo"},
        {"target": "categories", "source": "pond5_cat"},
    ],

    "GettyImages": [
        {"target": "file name", "source": "filename"},
        {"target": "created date", "source": "year"},
        {"target": "description", "source": "description"},
        {"target": "country", "source": "location"},
        {"target": "brief code", "value": ""},
        {"target": "title", "source": "title"},
        {"target": "keywords", "source": "keywords"},
        {"target": "categories", "source": "getty_cat"},
    ],

    "Alamy": [
        {"target": "Filename", "source": "filename"},
        {"target": "Caption", "source": "title"},
        {"target": "Tags", "source": "keywords"},
        {"target": "License type", "source": "editorial", "transform": license_type_from_editorial},
        {"target": "Username", "source": "username"},
        {"target": "Super Tags", "source": "super_keywords"},
        {"target": "Location", "source": "location"},
        {"target": "Date taken", "source": "year"},
        {"target": "Number of People", "source": "keywords", "transform": check_people},
        {"target": "Model release", "value": "NA"},
        {"target": "Is there property in this image", "source": "keywords", "transform": check_property},
        {"target": "Property release", "value": "NA"},
        {"target": "Primary category", "source": "primary_category"},
        {"target": "Secondary category", "source": "secondary_category"},
        {"target": "Image Type", "value": "P"},
        {"target": "Exclusive to Alamy", "value": "N"},
        {"target": "Additional Info", "value": ""},
    ]
}

def get_column_map(bank: str) -> BankColumnMap:
    """
    Vrátí mapu sloupců pro danou banku.

    Args:
        bank: Název banky

    Returns:
        Mapa sloupců pro danou banku
    """
    return BANK_COLUMN_MAPS.get(bank, [])
