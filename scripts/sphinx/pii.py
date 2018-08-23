"""
A Sphinx plugin that finds and lists places in the code that
report as having PII.
"""
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.locale import _


class Pii(nodes.Admonition, nodes.Element):
    pass


class PiiList(nodes.General, nodes.Element):
    pass


class PiilistDirective(Directive):
    def run(self):
        return [PiiList('')]


class PiiDirective(Directive):
    # this enables content in the directive
    has_content = True

    def run(self):
        env = self.state.document.settings.env

        targetid = "pii-%d" % env.new_serialno('pii')
        targetnode = nodes.target('', '', ids=[targetid])

        pii_node = Pii('\n'.join(self.content))
        pii_node += nodes.title(_('Pii'), _('Pii'))
        self.state.nested_parse(self.content, self.content_offset, pii_node)

        if not hasattr(env, 'pii_all_piis'):
            env.pii_all_piis = []
        env.pii_all_piis.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'pii': pii_node.deepcopy(),
            'target': targetnode,
        })

        return [targetnode, pii_node]


def visit_pii_node(self, node):
    self.visit_admonition(node)


def depart_pii_node(self, node):
    self.depart_admonition(node)


def purge_piis(app, env, docname):
    if not hasattr(env, 'pii_all_piis'):
        return
    env.pii_all_piis = [pii for pii in env.pii_all_piis if pii['docname'] != docname]


def process_pii_nodes(app, doctree, fromdocname):
    if not app.config.pii_include_piis:
        for node in doctree.traverse(Pii):
            node.parent.remove(node)

    # Replace all PiiList nodes with a list of the collected todos.
    # Augment each pii with a backlink to the original location.
    env = app.builder.env

    for node in doctree.traverse(PiiList):
        if not app.config.pii_include_piis:
            node.replace_self([])
            continue

        content = []

        for pii_info in env.pii_all_piis:
            para = nodes.paragraph()
            filename = env.doc2path(pii_info['docname'], base=None)
            description = (
                _('%s, line %d: ') %
                (filename, pii_info['lineno']))
            para += nodes.Text(description, description)

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_('view'), _('view'))
            newnode['refdocname'] = pii_info['docname']
            newnode['refuri'] = app.builder.get_relative_uri(
                fromdocname, pii_info['docname'])
            newnode['refuri'] += '#' + pii_info['target']['refid']
            newnode.append(innernode)
            para += newnode

            # Insert into the PiiList
            content.append(para)
            content.append(pii_info['pii'])

        node.replace_self(content)


def setup(app):
    app.add_config_value('pii_include_piis', True, 'html')

    app.add_node(PiiList)
    app.add_node(Pii,
                 html=(visit_pii_node, depart_pii_node),
                 latex=(visit_pii_node, depart_pii_node),
                 text=(visit_pii_node, depart_pii_node))

    app.add_directive('pii', PiiDirective)
    app.add_directive('piilist', PiilistDirective)
    app.connect('doctree-resolved', process_pii_nodes)
    app.connect('env-purge-doc', purge_piis)

    return {'version': '0.1'}   # identifies the version of our extension
