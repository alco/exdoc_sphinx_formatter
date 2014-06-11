defmodule ExDoc.Formatter.SPHINX do
  @moduledoc """
  Provide Sphnix-compatible reST documentation
  """

  alias ExDoc.Formatter.Sphinx.Templates
  alias ExDoc.Formatter.Sphinx.Autolink

  @default_opts [
    html_type: "html",
    html_theme: "default",
    pygments_style: "default",
  ]

  @doc """
  Generate Sphinx documentation for the given modules
  """
  def run(modules, config)  do
    config = Map.update!(config, :formatter_opts, &Keyword.merge(@default_opts, &1))

    output = Path.expand(config.output)
    ref_output = Path.join(output, "ref")
    :ok = File.mkdir_p ref_output

    all = Autolink.all(modules)
    modules    = filter_list(:modules, all)
    exceptions = filter_list(:exceptions, all)
    protocols  = filter_list(:protocols, all)

    generate_sphinx_scaffold(output, config)

    if config.formatter_opts[:gen_overview] do
      generate_overview(modules, exceptions, protocols, ref_output, config)
    end
    generate_list(:modules, modules, all, ref_output, config)
    generate_list(:exceptions, exceptions, all, ref_output, config)
    generate_list(:protocols, protocols, all, ref_output, config)

    html_type = config.formatter_opts[:html_type]
    build_sphinx_docs(output, html_type)

    Path.join([config.output, "_build", html_type, "index.html"])
  end

  @mix_appname Mix.Project.config[:app]
  @mix_version Mix.Project.config[:version]

  defp generate_sphinx_scaffold(output, config) do
    readme = if config.readme do
      content = File.read!(config.readme)
      rst = ExDoc.Markdown.Pandoc.convert_markdown(content, "rst", 1)
      File.write!(Path.join(output, "README.rst"), rst)
      [_, readme] = Regex.run(~r/(.+?).[^.]+$/, config.readme)
      readme
    end

    content = Templates.conf_template(config)
    :ok = File.write(Path.join(output, "conf.py"), content)

    content = Templates.index_template(readme)
    :ok = File.write(Path.join(output, "index.rst"), content)

    content = Templates.ref_template()
    :ok = File.write(Path.join(output, "ref.rst"), content)

    archive_name = Mix.Archive.name(@mix_appname, @mix_version)
    priv_dir = List.to_string(:code.priv_dir(:sphinx_formatter))
    verbatim_files = ["Makefile", "elixir_domain.py"]
    cp_fun = if String.contains?(priv_dir, archive_name) do
      &copy_from_archive(priv_dir, archive_name, output, &1)
    else
      &File.cp!(Path.join(priv_dir, &1), Path.join(output, &1))
    end
    Enum.each(verbatim_files, cp_fun)
  end

  def build_sphinx_docs(output, html_type) do
    File.cd!(output)
    System.cmd("make #{html_type}")
  end

  defp copy_from_archive(priv_dir, archive_name, output, filename) do
    {left, [^archive_name|right] } =
      Path.split(priv_dir) |> Enum.split_while(&( &1 != archive_name ))

    archive_path = Path.join(left) |> Path.join(archive_name) |> String.to_char_list
    file_relpath = Path.join(right) |> Path.join(filename) |> String.to_char_list

    {:ok, zip} = :zip.zip_open(archive_path, [:memory])
    {:ok, {^file_relpath, content}} = :zip.zip_get(file_relpath, zip)
    File.write!(Path.join(output, filename), content)
    :ok = :zip.zip_close(zip)
  end

  defp generate_overview(modules, exceptions, protocols, output, config) do
    content = Templates.overview_template(config, modules, exceptions, protocols)
    :ok = File.write("#{output}/overview.rst", content)
  end

  #defp assets do
    #[{ templates_path("css/*.css"), "css" },
     #{ templates_path("js/*.js"), "js" }]
  #end

  #defp generate_assets(output, _config) do
    #Enum.each assets, fn({ pattern, dir }) ->
      #output = "#{output}/#{dir}"
      #File.mkdir output

      #Enum.map Path.wildcard(pattern), fn(file) ->
        #base = Path.basename(file)
        #File.copy file, "#{output}/#{base}"
      #end
    #end
  #end

  #defp generate_readme(output, config) do
    #File.rm("#{output}/README.html")
    #write_readme(output, File.read("README.md"), config)
  #end

  #defp write_readme(output, {:ok, content}, config) do
    #readme_html = Templates.readme_template(config, content)
    ## Allow using nice codeblock syntax for readme too.
    #readme_html = String.replace(readme_html, "<pre><code>",
                                 #"<pre class=\"codeblock\"><code>")
    #File.write("#{output}/README.html", readme_html)
    #true
  #end

  #defp write_readme(_, _, _) do
    #false
  #end

  @doc false
  # Helper to split modules into different categories.
  #
  # Public so that code in Template can use it.
  def categorize_modules(nodes) do
    [modules: filter_list(:modules, nodes),
     exceptions: filter_list(:exceptions, nodes),
     protocols: filter_list(:protocols, nodes)]
  end

  defp filter_list(:modules, nodes) do
    Enum.filter nodes, &match?(%ExDoc.ModuleNode{type: x} when not x in [:exception, :protocol, :impl], &1)
  end

  defp filter_list(:exceptions, nodes) do
    Enum.filter nodes, &match?(%ExDoc.ModuleNode{type: x} when x in [:exception], &1)
  end

  defp filter_list(:protocols, nodes) do
    Enum.filter nodes, &match?(%ExDoc.ModuleNode{type: x} when x in [:protocol], &1)
  end

  defp generate_list(scope, nodes, all, output, config) do
    Enum.each nodes, &generate_module_page(&1, all, output, config)
    #content = Templates.list_page(scope, nodes, config, has_readme)
    #File.write("#{output}/#{scope}_list.rst", content)
  end

  defp generate_module_page(node, modules, output, config) do
    content = Templates.module_page(node, config, modules)
    content = Autolink.add_links(content, node, modules)
    File.write("#{output}/#{node.id}.rst", content)
  end

  #defp templates_path(other) do
    #Path.expand("html_formatter/templates/#{other}", __DIR__)
  #end
end
