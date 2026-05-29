# Custom key/value storage libary for cross-platform compatibility
# Provides a simple cross-platform storage API
import platform
import pathlib as pl
import json
import sys, os

class _BaseHandler:
    # Base handler interface for storage implementations
    def __init__(self):
        # Base Storage Handler
        pass

    def get(self, key, default=None): ...
    def set(self, key, value): ...
    def remove(self, key): ...


class _DesktopHandler(_BaseHandler):
    # Desktop file-based save handler
    def __init__(self):
        # Desktop Storage Handler
        _path: pl.Path
        _data: dict

        match platform.system():
            case "Windows":
                self._path = pl.Path(os.environ.get("APPDATA") + "\LawsonConallin\MWBI\.save")

            case  "Linux":
                self._path = pl.Path("~/.config/MWBI/.save")

            case _: # else, save next to the executable
                self._path = pl.Path(".save")

        if not self._path.exists():
            # create folders
            try: os.makedirs(os.environ.get("APPDATA") + "\LawsonConallin\MWBI")
            except FileExistsError: pass # folder already exists
            # create file
            with self._path.open("x") as f: f.close()
            json.dump({"_ver":"v0.0.0"}, self._path.open("w")) # dump an empty json dict

        # load file
        self._data = json.load(self._path.open())

        super().__init__()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
    
    def remove(self, key):
        del self._data[key]

class _WASMHandler(_BaseHandler):
    # WebAssembly / browser storage handler (placeholder)
    pass

class Storage:
    # Platform-aware storage wrapper
    base: _BaseHandler
    def __init__(self):
        match platform.system():
            case "Windows" | "Linux" | "MacOS":
                # Desktop: use savefile
                self.base = _DesktopHandler()
            case "Emscripten":
                # WASM: use LocalStorage
                self.base = _WASMHandler()

    def set(self, key: str, value: str | int | list | dict):
        self.base.set(key, value)

    def get(self, key: str):
        return self.base.get(key)

    def remove(self, key: str):
        self.base.remove(key)

    def cloudWrite(credentials):
        pass

    def cloudRestore(credentials):
        pass


class AssetManager:
    # Simple asset path manager for game assets
    _inventory: dict = {}

    def __init__(self, inventory: dict):
        for key in inventory.keys():
            value = inventory[key]
            if pl.Path(f"assets/{value}").exists():
                self._inventory.update({key: pl.Path(value)})
            else:
                raise Exception("Missing asset '%s' at '%s'".format(key, pl.Path("assets/%s".format(value)).absolute()))

    def get(self, asset_key: str):
        # Return asset path for a given key
        return pl.Path(f"assets/{self._inventory.get(asset_key)}")

    def get_path(self, path: str):
        return pl.Path(f"assets/{path}")