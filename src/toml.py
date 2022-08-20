try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def main():
    with open("gqrx.toml", mode="rb") as fp:
        config = tomllib.load(fp)

        print(config)


if __name__ == '__main__':
    main()
