import sys


def main() -> None:
    from .core import _main
    sys.exit(_main())


if __name__ == "__main__":
    main()
