"""
Performance-oriented tests for _is_not_edited filter.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(package_root))

from exportpreparedmedia import _is_not_edited


def test_is_not_edited_bulk():
    items = [{"Cesta": f"C:/photos/file_{i}.jpg"} for i in range(500)]
    results = [_is_not_edited(item) for item in items]
    assert all(results)
