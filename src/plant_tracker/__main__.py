"""Run the app: `uv run plant-tracker` or `python -m plant_tracker`."""

import os

from . import create_app


def main() -> None:
    app = create_app()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Plant Tracker running on http://localhost:{port} (database: {app.config['DATABASE']})")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
