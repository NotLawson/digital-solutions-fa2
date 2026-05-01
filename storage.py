# Custom key/value storage libary for cross-platform compatibility
import platform
import pathlib as pl
import json
import sys, os

class _BaseHandler:
    def __init__(self):
        # Base Storage Handler
        pass

class _DesktopHandler(_BaseHandler):
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
    pass

class Storage:
    # Storage handler for cross-platform construction
    base: _BaseHandler
    def __init__(self):
        match platform.system():
            case "Windows" | "Linux" | "MacOS":
                # Desktop: use savefile
                self.base = _DesktopHandler()
            case "Emscripten":
                # WASM: use LocalStorage
                self.base = _WASMHandler()

    def set(key: str, value: str | int | list | dict):
        pass

    def get(key: str):
        pass

    def remove(key: str):
        pass

    def cloudWrite(credentials):
        pass

    def cloudRestore(credentials):
        pass