defmodule SphinxFormatter.Mixfile do
  use Mix.Project

  def project do
    [app: :exdoc_sphinx_formatter,
     version: "0.5.0-beta",
     elixir: "~> 0.14.0",
     deps: deps]
  end

  defp deps do
    [{:ex_doc, in_umbrella: true}]
  end
end
