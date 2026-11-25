import os
from contextlib import closing

from .app import create_app
from .database import open_database


def main() -> None:
    with closing(open_database()) as db:
        create_app(db).run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))


if __name__ == "__main__":
    main()
