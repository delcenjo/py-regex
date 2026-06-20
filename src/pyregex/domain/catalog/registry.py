"""Central registry for the YAML regex catalog.

Handles discovery, loading, and indexed access to all categorized regex definitions.
"""

from __future__ import annotations
import os
import yaml
import logging

logger = logging.getLogger(__name__)
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CatalogEntry:
    """Represents a single regex definition in the catalog."""
    name: str
    category: str
    class_name: str
    description: str
    subtypes: Dict[str, Any]
    wizard: Dict[str, Any] = field(default_factory=dict)
    logic_handler: Optional[str] = None  # Path to a Python class for complex logic
    tags: List[str] = field(default_factory=list)
    source_file: str = ""
    config_schema: Dict[str, Any] = field(default_factory=dict)

    def is_complex(self) -> bool:
        """Returns True if this entry requires a custom Python handler."""
        return bool(self.logic_handler)

    @property
    def default_subtype(self) -> str:
        return list(self.subtypes.keys())[0] if self.subtypes else "standard"


class CatalogRegistry:
    """Manages the lifecycle and discovery of catalog entries."""

    def __init__(self, catalog_dir: Optional[Path] = None):
        if catalog_dir is None:
            catalog_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "catalog"
            if not catalog_dir.exists():
                catalog_dir = Path("catalog").resolve()
        
        self.catalog_dir = catalog_dir
        self._entries: Dict[str, CatalogEntry] = {}
        self._discovery_map: Dict[str, Path] = {} # entry_name -> file_path
        self._categories: Dict[str, List[str]] = {}
        self._tree: Dict[str, Any] = {} # Hierarchical tree
        self._expanded_paths: set[Path] = set()
        self._fast_scanned = False

    def _ensure_discovered(self, parts: Optional[list[str]] = None):
        """Lazily expands the tree level by level based on requested path."""
        if not self.catalog_dir.exists():
            return
        
        # 1. Always ensure root is scanned
        self._scan_dir(self.catalog_dir, self._tree, "")
        
        if not parts:
            return

        # 2. Walk down parts and scan each level if needed
        current_node = self._tree
        current_path = self.catalog_dir
        for i, part in enumerate(parts):
            if part not in current_node:
                break
            
            current_path = current_path / part
            current_node = current_node[part]
            # The category is the top-level directory
            category = parts[0]
            self._scan_dir(current_path, current_node, category)

    def _scan_dir(self, dir_path: Path, node: dict, category: str):
        """Scans a single directory level and adds it to the tree."""
        if dir_path in self._expanded_paths:
            return
            
        try:
            for entry in os.scandir(dir_path):
                if entry.is_dir():
                    if entry.name not in node:
                        node[entry.name] = {"__entries__": []}
                elif entry.is_file() and entry.name.endswith((".yaml", ".yml")):
                    path = Path(entry.path)
                    self._peek_entries(path, category, node)
        except Exception as e:
            logger.warning("Directory scanning failed %s: %s", dir_path, e)
            
        self._expanded_paths.add(dir_path)

    def _peek_entries(self, path: Path, category: str, tree_node: Dict[str, Any]):
        """Peeks at entry names in a file for discovery."""
        try:
            # OPTIMIZATION: Instead of safe_load, we can use simple string matching 
            # for the first few lines to detect v2.0 and name.
            with open(path, "r", encoding="utf-8") as f:
                head = f.read(512)
            
            if "version: \"2.0\"" in head or "metadata:" in head:
                # Renaissance v2.0
                name = path.parent.name
                self._discovery_map[name] = path
                self._add_to_categories(name, category)
                if name not in tree_node["__entries__"]:
                    tree_node["__entries__"].append(name)
                return

            # Fallback to full parse for legacy files or unknown
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return

            if "entries" in data:
                for item in data["entries"]:
                    name = item.get("name")
                    if name:
                        self._discovery_map[name] = path
                        self._add_to_categories(name, category)
                        if name not in tree_node["__entries__"]:
                            tree_node["__entries__"].append(name)
        except Exception as e:
            logger.warning("Peek entries failed for %s: %s", path, e)

    def _add_to_categories(self, name: str, category: str):
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)

    def ensure_loaded(self):
        """Deprecated: Use get_entry for lazy loading."""
        self._ensure_discovered()

    def _load_entry(self, name: str):
        """Loads a specific entry and its siblings from its source file."""
        if name in self._entries:
            return

        path = self._discovery_map.get(name)
        if not path:
            return

        try:
            rel_path = path.relative_to(self.catalog_dir)
            category = rel_path.parts[0] if rel_path.parts else path.parent.name
            
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data:
                return

            if "entries" in data:
                # Legacy v1.0
                for item in data["entries"]:
                    entry_name = item.get("name")
                    if not entry_name: continue
                    self._entries[entry_name] = self._create_entry_v1(item, category, path)
            elif data.get("version") == "2.0" or "metadata" in data:
                # Renaissance v2.0
                self._entries[name] = self._create_entry_v2(name, data, category, path)
                
        except Exception as e:
            logger.warning("Load entry failed %s: %s", name, e)

    def _create_entry_v1(self, item: dict, category: str, path: Path) -> CatalogEntry:
        return CatalogEntry(
            name=item.get("name", ""),
            category=category,
            class_name=item.get("class_name", ""),
            description=item.get("description", ""),
            subtypes=item.get("subtypes", {}),
            wizard=item.get("wizard", {}),
            logic_handler=item.get("logic_handler"),
            tags=item.get("tags", []),
            source_file=str(path),
            config_schema=item.get("config_schema", {})
        )

    def _create_entry_v2(self, name: str, data: dict, category: str, path: Path) -> CatalogEntry:
        metadata = data.get("metadata", {})
        wizard_cfg = data.get("wizard", {})
        logic = data.get("logic", {})
        corpus = data.get("corpus", {})
        
        # Map v2.0 'logic' and 'corpus' into 'subtypes' for compatibility.
        examples = [m["value"] for m in corpus.get("matches", []) if "value" in m]
        non_examples = [m["value"] for m in corpus.get("non_matches", []) if "value" in m]
        
        # Metadata fix: Ensure the title is used as display_name if not explicitly set in wizard
        if "display_name" not in wizard_cfg and "title" in metadata:
            wizard_cfg["display_name"] = metadata["title"]

        subtypes = {
            "standard": {
                "pattern": logic.get("base_pattern", ""),
                "examples": examples,
                "non_examples": non_examples
            }
        }
        
        # Add variants as subtypes
        for variant in logic.get("variants", []):
            v_id = variant.get("id")
            if v_id:
                subtypes[v_id] = {
                    "pattern": variant.get("pattern", logic.get("base_pattern", "")),
                    "examples": examples, # Reuse examples for now
                    "non_examples": non_examples
                }

        return CatalogEntry(
            name=name,
            category=category,
            class_name=metadata.get("title", name),
            description=metadata.get("description", ""),
            subtypes=subtypes,
            wizard=wizard_cfg,
            logic_handler=data.get("logic_handler"),
            tags=metadata.get("tags", []),
            source_file=str(path),
            config_schema=data.get("config_schema", {}) 
        )

    def get_entry(self, name: str) -> Optional[CatalogEntry]:
        """Returns a single entry by its unique name, loading it lazily."""
        if not self._fast_scanned:
            self._ensure_discovered()
        if name not in self._entries:
            self._load_entry(name)
        return self._entries.get(name)

    def list_at_path(self, path_parts: list[str]) -> tuple[list[str], list[str]]:
        """Returns (subfolders, entries) at the given catalog path."""
        if not self._fast_scanned:
            self._ensure_discovered(path_parts)
        
        current_node = self._tree
        for part in path_parts:
            if part in current_node:
                current_node = current_node[part]
            else:
                return [], []
        
        subfolders = [k for k in current_node.keys() if k != "__entries__"]
        entries = current_node.get("__entries__", [])
        return sorted(subfolders), sorted(entries)

    def fast_scan(self):
        """Ultra-fast industrial discovery of all catalog entries without file parsing."""
        if not self.catalog_dir.exists():
            return
            
        # 1. Clear previous discovery state to prevent duplicates
        self._discovery_map.clear()
        self._categories.clear()
        self._expanded_paths.clear()
        self._tree = {}
        
        catalog_path_str = str(self.catalog_dir)
        sep = os.sep

        # root/category/sub/sub/leaf/index.yaml
        for root, dirs, files in os.walk(catalog_path_str):
            yaml_files = [f for f in files if f.endswith((".yaml", ".yml"))]
            if not yaml_files:
                continue
                
            rel_path_str = root[len(catalog_path_str):]
            if rel_path_str.startswith(sep):
                rel_path_str = rel_path_str[len(sep):]
            
            if rel_path_str:
                parts = rel_path_str.split(sep)
            else:
                parts = []
                
            # If there's a yaml file, the folder name is the entry ID (v2.0)
            entry_name = os.path.basename(root)
            category = parts[0] if parts else entry_name
            
            primary_yaml = Path(root) / yaml_files[0]
            self._discovery_map[entry_name] = primary_yaml
            self._add_to_categories(entry_name, category)
            
            # Populate the tree for navigation
            current_node = self._tree
            for part in parts:
                if part not in current_node:
                    current_node[part] = {"__entries__": []}
                # If we're at the leaf folder, add to entries
                if part == entry_name:
                    if entry_name not in current_node["__entries__"]:
                        current_node["__entries__"].append(entry_name)
                current_node = current_node[part]
        
        self._fast_scanned = True

    def list_categories(self) -> List[str]:
        """Returns a list of all discovered categories."""
        # If not already discovered by fast_scan, do a quick root scan
        if not self._fast_scanned and not self._tree:
            self._ensure_discovered()
        
        # Include both file-identified categories AND top-level folder categories
        cats = set(self._categories.keys())
        cats.update([k for k in self._tree.keys() if k != "__entries__"])
        return sorted(list(cats))

    def list_entries(self, category: Optional[str] = None) -> List[str]:
        """Returns entries, optionally filtered by category."""
        if category:
            if not self._fast_scanned:
                self._ensure_discovered(parts=[category])
            return sorted(self._categories.get(category, []))
        
        if not self._fast_scanned:
            self._ensure_discovered()
        return sorted(list(self._discovery_map.keys()))

    def search(self, query: str) -> List[CatalogEntry]:
        """Search entries by name or tag."""
        self.ensure_loaded()
        query = query.lower()
        results = []
        for entry in self._entries.values():
            if query in entry.name.lower() or any(query in t.lower() for t in entry.tags):
                results.append(entry)
        return results


# Global singleton
catalog_registry = CatalogRegistry()
