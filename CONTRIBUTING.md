# Contributing

## Dev setup

- `poetry`: `unweaver` uses the `poetry` library to manage dependencies, release, and other parts
of package management. Please use `poetry` if you plan on making contributions that
involve adding new Python dependencies. `poetry` will also make it very easy for you to
get up and running with exactly the right packages: just use `poetry install`.

- `black`: `unweaver` uses the `black` autoformatter to manage style formatter. The
best part of using `black` is that you don't have to worry about how you personally
style your code while writing: `black` will make it contribution-ready for you.

- `pre-commit`: `pre-commit` will automatically run `black` for every commit you make,
ensuring that you never have to worry about style formatting. It will be installed
already if you used `poetry` to install the dev depencies. Just run `pre-commit
install` one time in the project directory. If you're using `poetry`, make sure to use
the correct environment by running `poetry run pre-commit install`.
