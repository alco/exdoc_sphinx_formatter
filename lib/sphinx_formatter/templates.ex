defmodule ExDoc.Formatter.Sphinx.Templates do
  @moduledoc """
  Handle all template interfaces for the HTML formatter.
  """

  require EEx

  @doc """
  Generate content from the module template for a given `node`
  """
  def module_page(node, config, all) do
    types       = node.typespecs
    functions   = Enum.filter node.docs, &match?(%ExDoc.FunctionNode{type: :def}, &1)
    macros      = Enum.filter node.docs, &match?(%ExDoc.FunctionNode{type: :defmacro}, &1)
    callbacks   = Enum.filter node.docs, &match?(%ExDoc.FunctionNode{type: :defcallback}, &1)
    module_template(config, node, types, functions, macros, callbacks, all)
  end

  # Get the full specs from a function, already in HTML form.
  defp get_specs(%ExDoc.FunctionNode{specs: specs}) when is_list(specs) do
    presence specs
  end

  defp get_specs(_node), do: nil

  # Convert markdown to HTML.
  defp md2rst(bin), do: md2rst(bin, 1)
  defp md2rst(nil, _), do: ""
  defp md2rst(bin, lvl), do: ExDoc.Markdown.Pandoc.convert_markdown(bin, "rst", lvl)

  defp indent(n, str) do
    str
    |> String.split("\n")
    |> Enum.map(&(String.duplicate(" ", n) <> &1))
    |> Enum.join("\n")
  end

  # Get the pretty name of a function node
  defp pretty_type(%ExDoc.FunctionNode{type: t}) do
    case t do
      :def          -> "function"
      :defmacro     -> "macro"
      :defcallback  -> "callback"
    end
  end

  defp pretty_x_ref(%ExDoc.FunctionNode{id: name}) do
    ":elixir:func:`#{esc_ref name}`"
  end

  # Get the first paragraph of the documentation of a node, if any.
  def synopsis(nil), do: ""
  def synopsis(doc) do
    String.split(doc, ~r/\n\s*\n/)
    |> hd
    |> String.strip()
    |> String.rstrip(?.)
    |> md2rst
    |> String.replace("\n", " ")
  end

  # A bit of standard HTML to insert the to-top arrow.
  defp to_top_link() do
    "<a class=\"to_top_link\" href=\"#content\" title=\"To the top of the page\">&uarr;</a>"
  end

  defp presence([]),    do: nil
  defp presence(other), do: other

  defp h(binary) do
    escape_map = [{ ~r(&), "\\&amp;" }, { ~r(<), "\\&lt;" }, { ~r(>), "\\&gt;" }, { ~r("), "\\&quot;" }]
    Enum.reduce escape_map, binary, fn({ re, escape }, acc) -> Regex.replace(re, acc, escape) end
  end

  ## Get the breadcrumbs HTML.
  ##
  ## If module is :overview generates the breadcrumbs for the overview.
  #defp module_breadcrumbs(config, modules, module) do
    #parts = [root_breadcrumbs(config), { "Overview", "overview.html" }]
    #aliases = Module.split(module.module)
    #modules = Enum.map(modules, &(&1.module))

    #{ crumbs, _ } =
      #Enum.map_reduce(aliases, [], fn item, parents ->
        #path = parents ++ [item]
        #mod  = Module.concat(path)
        #page = if mod in modules, do: inspect(mod) <> ".html"
        #{ { item, page }, path }
      #end)

    #generate_breadcrumbs(parts ++ crumbs)
  #end

  #defp page_breadcrumbs(config, title, link) do
    #generate_breadcrumbs [root_breadcrumbs(config), { title, link }]
  #end

  #defp root_breadcrumbs(config) do
    #{ "#{config.project} v#{config.version}", nil }
  #end

  #defp generate_breadcrumbs(crumbs) do
    #Enum.map_join(crumbs, " &rarr; ", fn { name, ref } ->
      #if ref, do: "<a href=\"#{h(ref)}\">#{h(name)}</a>", else: h(name)
    #end)
  #end

  templates = [
    #list_template: [:scope, :nodes, :config, :has_readme],
    overview_template: [:config, :modules, :exceptions, :protocols],
    module_template: [:config, :module, :types, :functions, :macros, :callbacks, :all],
    #list_item_template: [:node],
    detail_template: [:node, :module],
    type_detail_template: [:node, :module],
  ]
  scaffold_templates = [
    index_template: {"index.rst.eex", [:readme]},
    conf_template: {"conf.py.eex", [:config]},
    ref_template: {"ref.rst.eex", []},
  ]

  Enum.each templates, fn({ name, args }) ->
    filename = Path.expand("templates/#{name}.eex", __DIR__)
    EEx.function_from_file :def, name, filename, args
  end

  Enum.each scaffold_templates, fn({ name, {filename, args} }) ->
    path = Path.join([__DIR__, "templates/scaffold", filename])
    EEx.function_from_file :def, name, path, args
  end


  defp adorn_title(title) do
    title <> "\n" <> String.replace(title, ~r".", "=")
  end

  defp render_overview_table(nodes) do
    Enum.map(nodes, fn node ->
      {":elixir:mod:`#{esc node.id}`", synopsis(node.moduledoc)}
    end) |> render_table()
  end

  defp render_summary_table(nodes) do
    Enum.map(nodes, fn node ->
      {pretty_x_ref(node), synopsis(node.doc)}
    end) |> render_table()
  end

  defp render_table(rows) do
    longest_name_len =
      rows |> Enum.map(fn {left, _} -> String.length left end) |> Enum.max
    table_delim = String.duplicate("=", longest_name_len) <> " ="
    rows = Enum.map(rows, fn {left, right} ->
      :io_lib.format('~-*.s ~s~n', [longest_name_len, left, right])
      |> List.to_string
    end)
    table_delim <> "\n" <> Enum.join(rows, "\n") <> table_delim
  end

  defp esc(text) do
    text
    #|> String.replace("\\", "\\\\")
    |> String.replace("|", "\\|")
  end

  defp esc_ref(text) do
    text
    |> String.replace("!", "\\!")
  end

  # This is needed to make Sphinx render headers in function descriptions.
  # We replace headers that have indent with bold paragraphs.
  defp transform_headers(text) do
    Regex.replace(~r"^(\s+)(.+)\n\1\^\^\^+\n"m, text, "\\1**\\2**\n")
  end
end
