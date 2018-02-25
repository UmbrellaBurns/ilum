import os
from ilum.templates.base import Template
from ilum.templates import config


def render_template(template_name, **kwargs):
    kwargs.update({"static": config["static"]})

    with open(os.path.join(config["templates"], template_name), 'r', encoding='utf-8') as f:
        template_body = f.read()

    return Template(template_body).render(**kwargs)
