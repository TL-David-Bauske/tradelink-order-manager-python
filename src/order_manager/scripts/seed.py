from contextlib import closing

from ..database import open_database
from ..seed import seed_database


def main() -> None:
    with closing(open_database()) as db:
        seed_database(db)
    print("Seeded three products and three warehouses.")


if __name__ == "__main__":
    main()
