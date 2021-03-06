SphinxFormatter
===============

This is a custom formatter for [ExDoc][1].

  [1]: https://github.com/elixir-lang/ex_doc


## Prerequisites

SphinxFormatter relies on `pandoc` (command-line tool) and Sphinx (Python
package) to work. Sphinx also uses a Makefile in its build process, so make
sure you have `make` installed and working on your system.


## Usage

To be able to use the formatter with ExDoc, it needs to be added to the load
path prior to running `ex_doc` command-line tool or the `mix docs` tasks. The
Mix task is more convenient and it has a nice property to it: Mix automatically
adds all locally installed archives to the load path before running any
commands.

We can exploit that by doing `mix archive` inside the formatter's project root
and then `mix local.install` the resulting .ez file.

If you'd like to give it a try, you can grab the prebuilt archive from this
[url][archive_url]. Just run `mix local.install <url>`. It is compatible with
Elixir v0.14.0 and ExDoc master (or this prebuilt [ExDoc
archive][exdoc_archive_url]). See this [mix.exs file][config_url] for an
example of possible config values.

The ExDoc archive mentioned above can also be used to build docs with the stock
HTML formatter. You don't need to set any config options to start using it,
just run `mix docs` inside any mix project.

  [archive_url]: https://github.com/alco/exdoc_sphinx_formatter/releases/download/v0.14.0/exdoc_sphinx_formatter-0.5.0-beta-0.14.0.ez
  [exdoc_archive_url]: https://github.com/alco/exdoc/releases/download/v0.14.0/ex_doc-master-0.14.0.ez
  [config_url]: https://github.com/alco/porcelain/blob/7d0b7e3d533c73030855759260431a673c44c474/mix.exs#L16-L29


## Development

In order to compile the formatter, you need to have ExDoc source handy. The
most convenient way to do this is to create an umbrella app with two apps:
ExDoc and the formatter:

    $ mix new exdoc_formatters --umbrella
    $ cd exdoc_formatters/apps
    $ git clone git@github.com:elixir-lang/ex_doc.git
    $ git clone git@github.com:alco/exdoc_sphinx_formatter.git

SphinxFormatter already has `:ex_doc` as an umbrella dependency in its
`mix.exs` file.
