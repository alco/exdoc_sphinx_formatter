from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType, Index
from sphinx.util.compat import Directive
from sphinx.util.nodes import make_refnode
#from sphinx.util.docfields import Field, TypedField


def _iteritems(d):
    for k in d:
        yield k, d[k]

class ElixirObject(ObjectDescription):
    def needs_arglist(self):
        print("needs_arglist")
        return self.objtype == 'function'

    def handle_signature(self, sig, signode):
        #print("handle_signature")
        #print(sig)
        #print(signode)
        header = nodes.title()
        header += nodes.Text(sig)
        #signode += header
        signode += addnodes.desc_name(sig, sig)
        return sig, "PREFIX"

    def get_index_text(self, modname, name_cls):
        """Return the text for the index entry of the object."""
        if self.objtype == 'function':
            if not modname:
                return _('%s() (built-in function)') % name_cls[0]
            return _('%s() (in module %s)') % (name_cls[0], modname)
        elif self.objtype == 'data':
            if not modname:
                return _('%s (built-in variable)') % name_cls[0]
            return _('%s (in module %s)') % (name_cls[0], modname)
        else:
            return ''

    def add_target_and_index(self, name, sig, signode):
        modname = ''
        fullname = (modname and modname + '.' or '') + name[0]
        # note target
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            objects = self.env.domaindata['elixir']['objects']
            if fullname in objects:
                self.state_machine.reporter.warning(
                    'duplicate object description of %s, ' % fullname +
                    'other instance in ' +
                    self.env.doc2path(objects[fullname][0]) +
                    ', use :noindex: for one of them',
                    line=self.lineno)
            objects[fullname] = (self.env.docname, self.objtype)

        indextext = self.get_index_text(modname, name)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname, ''))
        #print("add_target_and_index")
        #print(name)
        #print(sig)
        #print(signode)
        #print(dir(self))

class ElixirFunction(ElixirObject):
    option_spec = {
        'sig': directives.unchanged,
    }
    pretty_type = "(function)"

    def handle_signature(self, sig, signode):
        true_sig = self.options['sig']
        signode += addnodes.desc_name(true_sig, true_sig)
        signode += addnodes.desc_annotation(self.pretty_type, self.pretty_type)
        return sig, ""

class ElixirCallback(ElixirFunction):
    pretty_type = "(callback)"

class ElixirMacro(ElixirFunction):
    pretty_type = "(macro)"

class ElixirType(ElixirObject):
    def handle_signature(self, sig, signode):
        [name, _] = sig.split("/")
        comps = name.rsplit(".", 1)
        if len(comps) == 2:
            shortname = comps[1]
        else:
            shortname = name
        signode += addnodes.desc_name(shortname, shortname)
        return sig, ""

class ElixirModule(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'mtype': directives.unchanged,
    }

    def run(self):
        #print(self.content)

        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        noindex = 'noindex' in self.options
        env.temp_data['elixir:module'] = modname
        #print("Adding doc %s for module %s" % (env.docname, modname))
        env.domaindata['elixir']['modules'][modname] = \
            (env.docname, self.options.get('synopsis', ''),
             self.options.get('platform', ''), 'deprecated' in self.options)
        targetnode = nodes.target('', '', ids=['module-' + modname], ismod=True)
        self.state.document.note_explicit_target(targetnode)
        ret = [targetnode]
        # XXX this behavior of the module directive is a mess...
        if 'platform' in self.options:
            platform = self.options['platform']
            node = nodes.paragraph()
            node += nodes.emphasis('', _('Platforms: '))
            node += nodes.Text(platform, platform)
            ret.append(node)
        # the synopsis isn't printed; in fact, it is only used in the
        # modindex currently
        if not noindex:
            indextext = _('%s (module)') % modname
            inode = addnodes.index(entries=[('single', indextext,
                                             'module-' + modname, modname)])
            ret.append(inode)
        return ret

class ElixirXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        #print("=== PROCESS LINK ===")
        #if refnode['reftype'] == 'type':

        #print(refnode)
        #print(refnode['reftype'])
        #print(has_explicit_title)
        #print(title)
        #print(target)
        #print("====================")

        refnode['elixir:module'] = env.temp_data.get('elixir:module')
        if not has_explicit_title:
            title = title.lstrip(':')   # only has a meaning for the target
            target = target.lstrip('~') # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                colon = title.rfind(':')
                if colon != -1:
                    title = title[colon+1:]
        return title, target

class ElixirModuleIndex(Index):
    """
    Index subclass to provide the Elixir module index.
    """

    name = 'modindex'
    localname = l_('Elixir Module Index')
    shortname = l_('modules')

    def generate(self, docnames=None):
        content = {}
        # list of prefixes to ignore
        ignores = self.domain.env.config['modindex_common_prefix']
        ignores = sorted(ignores, key=len, reverse=True)
        # list of all modules, sorted by module name
        modules = sorted(_iteritems(self.domain.data['modules']),
                         key=lambda x: x[0].lower())
        # sort out collapsable modules
        prev_modname = ''
        num_toplevels = 0
        for modname, (docname, synopsis, platforms, deprecated) in modules:
            if docnames and docname not in docnames:
                continue

            for ignore in ignores:
                if modname.startswith(ignore):
                    modname = modname[len(ignore):]
                    stripped = ignore
                    break
            else:
                stripped = ''

            # we stripped the whole module name?
            if not modname:
                modname, stripped = stripped, ''

            entries = content.setdefault(modname[0].lower(), [])

            package = modname.split(':')[0]
            if package != modname:
                # it's a submodule
                if prev_modname == package:
                    # first submodule - make parent a group head
                    entries[-1][1] = 1
                elif not prev_modname.startswith(package):
                    # submodule without parent in list, add dummy entry
                    entries.append([stripped + package, 1, '', '', '', '', ''])
                subtype = 2
            else:
                num_toplevels += 1
                subtype = 0

            qualifier = deprecated and _('Deprecated') or ''
            entries.append([stripped + modname, subtype, docname,
                            'module-' + stripped + modname, platforms,
                            qualifier, synopsis])
            prev_modname = modname

        # apply heuristics when to collapse modindex at page load:
        # only collapse if number of toplevel modules is larger than
        # number of submodules
        collapse = len(modules) - num_toplevels < num_toplevels

        # sort by first letter
        content = sorted(_iteritems(content))

        return content, collapse


class ElixirDomain(Domain):
    """
    Elixir language domain.

    Derived from
    https://bitbucket.org/birkenfeld/sphinx-contrib/src/940757f22e335f6ae98521621201683d6bab1d60/erlangdomain/?at=default
    """
    name = 'elixir'
    label = 'Elixir'
    object_types = {
        'function': ObjType(l_('function'), 'func'),
        'callback': ObjType(l_('callback'), 'callb'),
        'macro':    ObjType(l_('macro'),    'macro'),
        'type':     ObjType(l_('macro'),    'type'),
        'module':   ObjType(l_('module'),   'mod'),
    }

    directives = {
        'function': ElixirFunction,
        'callback': ElixirCallback,
        'macro':    ElixirMacro,
        'type':     ElixirType,
        'module':   ElixirModule,
    }
    roles = {
        'func' :    ElixirXRefRole(),
        'callb':    ElixirXRefRole(),
        'macro':    ElixirXRefRole(),
        'type':     ElixirXRefRole(),
        'mod':      ElixirXRefRole(),
    }
    initial_data = {
        'objects': {},    # fullname -> docname, objtype
        'functions' : {}, # fullname -> arity -> (targetname, docname)
        'modules': {},    # modname -> docname, synopsis, platform, deprecated
    }
    indices = [
        ElixirModuleIndex,
    ]

    def clear_doc(self, docname):
        for fullname, (fn, _) in list(self.data['objects'].items()):
            if fn == docname:
                del self.data['objects'][fullname]
        for modname, (fn, _, _, _) in list(self.data['modules'].items()):
            if fn == docname:
                del self.data['modules'][modname]
        for fullname, funcs in list(self.data['functions'].items()):
            for arity, (fn, _) in list(funcs.items()):
                if fn == docname:
                    del self.data['functions'][fullname][arity]
            if not self.data['functions'][fullname]:
                del self.data['functions'][fullname]

    def find_module_docname(self, modname):
        if not modname:
            return

        module = self.data["modules"].get(modname)
        if not module:
            return

        return module[0]

    def _find_obj(self, env, modname, name, objtype, searchorder=0):
        """
        Find a Python object for "name", perhaps using the given module and/or
        classname.
        """
        if not name:
            return None, None
        if ":" not in name:
            name = "%s:%s" % (modname, name)

        if name in self.data['objects']:
            return name, self.data['objects'][name][0]

        if '/' in name:
            #print(repr(name))
            fname, arity = name.rsplit('/', 1)
            arity = int(arity)
        else:
            fname = name
            arity = -1
        if fname not in self.data['functions']:
            return None, None

        arities = self.data['functions'][fname]
        if arity == -1:
            arity = min(arities)
        if arity in arities:
             docname, targetname = arities[arity]
             return targetname, docname
        return None, None

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        #print("RESOLVE XREF")
        #print(env.docname)
        #print(fromdocname)
        #print(typ)
        #print(target)
        ##print(node)
        ##print(contnode)
        #print("..................")

        if typ == "type":

            #modname = node.get('elixir:module')
            #if modname is None:
                #print("MODNAME IS NONE")
                #print(env)
                #print(fromdocname)
                #print(typ)
                #print(target)
                #print(node)
                #return

            # target will be either "typename/0" or "Module.Name.typename/0"
            comps = target.rsplit(".", 1)
            if len(comps) == 2:
                docname = self.find_module_docname(comps[0])
                if not docname:
                    return
            else:
                docname = fromdocname
                modname = node.get('elixir:module')
                target = modname + "." + target
            text_node = contnode.children[0]
            # title becomes tooltip text in HTML output
            title = text_node.astext().split("/")[0]
            contnode.children[0] = nodes.Text(title)
            return make_refnode(builder, fromdocname, docname, target, contnode, title)

        if typ == "func":
            # target will be either "typename/0" or "Module.Name.typename/0"
            text_node = contnode.children[0]
            # title becomes tooltip text in HTML output
            title = text_node.astext()

            # Special case for the ~~~/1 operator
            if "~~" in title:
                target = "~~~/1"
                title = "~~~/1"

            comps = target.rsplit(".", 1)
            # special cases for ../2 and ./2
            if len(comps) == 2 and \
                    not ".." in target and \
                    not target.startswith("."):
                docname = self.find_module_docname(comps[0])
                if not docname:
                    return
            else:
                docname = fromdocname
                modname = node.get('elixir:module')
                target = modname + "." + target
            contnode.children[0] = nodes.Text(title)
            return make_refnode(builder, fromdocname, docname, target, contnode, title)

        if typ == 'mod' and target in self.data['modules']:
            docname, synopsis, platform, deprecated = \
                self.data['modules'].get(target, ('','','', ''))
            if not docname:
                return None
            else:
                title = '%s%s%s' % ((platform and '(%s) ' % platform),
                                    synopsis,
                                    (deprecated and ' (deprecated)' or ''))
                return make_refnode(builder, fromdocname, docname,
                                    'module-' + target, contnode, title)
        else:
            modname = node.get('elixir:module')
            searchorder = node.hasattr('refspecific') and 1 or 0
            name, obj = self._find_obj(env, modname, target, typ, searchorder)
            if not obj:
                return None
            else:
                return make_refnode(builder, fromdocname, obj, name,
                                    contnode, name)

    def get_objects(self):
        for refname, (docname, type) in _iteritems(self.data['objects']):
            yield (refname, refname, type, docname, refname, 1)


def setup(app):
    app.add_domain(ElixirDomain)
