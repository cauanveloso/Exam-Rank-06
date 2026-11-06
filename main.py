import sys

from src.simulator import main


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
