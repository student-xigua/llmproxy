# Vercel entry point
import os
import sys
from pathlib import Path

def load_routes():
    from fastapi import FastAPI
    from starlette.middleware.cors import CORSMiddleware
    import importlib.util

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Get the api directory
    base_dir = Path(__file__).parent
    v1_dir = base_dir / "v1"

    print(f"API base dir: {base_dir}")
    print(f"V1 dir: {v1_dir}")
    print(f"V1 dir exists: {v1_dir.exists()}")
    print(f"V1 files: {list(v1_dir.glob('*.py'))}")

    # Load v1 routes
    for path in sorted(v1_dir.glob("*.py")):
        if path.stem == "__init__":
            continue
        try:
            module_name = f"v1.{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            if hasattr(module, "router"):
                prefix = f"/v1/{path.stem}"
                app.include_router(module.router, prefix=prefix)
                print(f"Registered route: {prefix}")
        except Exception as e:
            print(f"Error loading {path}: {e}")
            raise

    return app

# Create app
app = load_routes()

__all__ = ["app"]
