#!/usr/bin/env python

import textwrap

import jinja2
import yaml


class GithubActionsYamlLoader(yaml.SafeLoader):

    @staticmethod
    def _unsupported(kind, token):
        return SyntaxError('Github Actions does not support %s:\n%s' % (kind, token.start_mark))

    def fetch_alias(self):
        super().fetch_alias()
        raise self._unsupported('aliases', self.tokens[0])

    def fetch_anchor(self):
        super().fetch_anchor()
        raise self._unsupported('anchors', self.tokens[0])


environment = jinja2.Environment(
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='<@',
    variable_end_string='@>',
    comment_start_string='<#',
    comment_end_string='#>',
    lstrip_blocks=True,
    trim_blocks=True,
)

with open('.github/workflows/ci/workflow_context.yml') as fp:
    context = yaml.load(fp, Loader=yaml.SafeLoader)
with open('.github/workflows/ci/workflow_template.yml') as fp:
    template = environment.from_string(fp.read())

for j in context['jobs']:
    base_type = j['type'].split('_')[0]
    j['id'] = '%s_%s' % (base_type, j['variant'].lower().replace(' ', '_').replace('.', ''))
    j['name'] = '%s (%s)' % (base_type.capitalize(), j['variant'])
    j['needs'] = j.get('needs', [])
    j['reqs'] = ['reqs/%s.txt' % r for r in j['reqs']]
    j['cache_extra_deps'] = j.get('cache_extra_deps', [])

# Render template.
workflow = template.render(context)

# Save result.
with open('.github/workflows/ci.yml', 'w') as fp:
    fp.write(textwrap.dedent(
        '''
        #
        # DO NOT MODIFY! AUTO-GENERATED FROM:
        # .github/workflows/ci/workflow_template.yml
        #

        ''').lstrip())
    fp.write(workflow)

# And try parsing it to check it's valid YAML,
# and ensure anchors/aliases are not used.
GithubActionsYamlLoader(workflow).get_single_data()
