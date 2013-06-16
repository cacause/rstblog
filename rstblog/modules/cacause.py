# -*- coding: utf-8 -*-
"""
    rstblog.modules.cacause
    ~~~~~~~~~~~~~~~~~~~~~~~

    The CaCause component.

    :copyright: (c) 2013 by CaCause Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import yaml
import hashlib
import six
from rstblog.signals import before_template_rendered
from StringIO import StringIO
from docutils import core
import jinja2

cacause_context = {}


def get_article_id(source_filename):
    m = hashlib.md5()
    m.update(source_filename)
    return m.hexdigest()


def read_comment(comment_file, header=True):
    content = ['---']
    f = open(comment_file, 'r')

    # read comment header
    for line in f:
        line = line.rstrip()
        if not line:
            break
        content.append(line)

    # read comment body
    if not header:
        content = []
        for line in f:
            line = line.rstrip()
            content.append(line.decode('utf-8'))
    f.close()

    # return header or body
    return content


def get_comment_meta(comment_file):
    headers = read_comment(comment_file)
    cfg = yaml.load(StringIO('\n'.join(headers)))
    if cfg:
        if not isinstance(cfg, dict):
            raise ValueError('expected dict config in file "%s", got: %.40r'
                % (comment_file, cfg))
    return cfg


def read_comments(comment_dir):
    cacause_context['comments'] = {}
    comment_files = os.listdir(comment_dir)
    for file in comment_files:
        absolute_comment_file = '/'.join([comment_dir, file])
        cfg = get_comment_meta(absolute_comment_file)
        cfg['comment'] = absolute_comment_file
        article_id = cfg['article']
        if article_id:
            if not article_id in cacause_context['comments']:
                cacause_context['comments'][article_id] = []
            cacause_context['comments'][article_id].append(cfg)


def rest_to_html_fragment(a_str):
    parts = core.publish_parts(
        source=a_str,
        writer_name='html')
    fragment = parts['body_pre_docinfo'] + parts['fragment']
    return jinja2.Markup(fragment.encode('utf-8'))


def enhance_template_context(template, context):
    if not 'ctx' in context:
        return

    # create cacause context if empty
    if not 'comments' in cacause_context:
        cacause_dir = context['config'].get('cacause_dir')
        if not cacause_dir:
            print "cacause: can't find cacause_dir in config.yml"
            sys.exit(1)
        read_comments("/".join(
            [context['builder'].project_folder, cacause_dir]))

    # add related comments to template context if any
    context['ctx'].comments = []
    article_id = get_article_id(context['source_filename'])
    if article_id in cacause_context['comments']:
        for comment_meta in cacause_context['comments'][article_id]:
            comment_body = read_comment(comment_meta['comment'], False)
            comment = comment_meta.copy()
            comment['body'] = rest_to_html_fragment('\n'.join(comment_body))
            context['ctx'].comments.append(comment)
            # add gravatar image
            use_gravatar = context['config'].get('cacause_gravatar')
            if use_gravatar:
                email = comment_meta['email']
                email_bytes = six.b(email).lower() if email else ''
                gravatar_url = "http://www.gravatar.com/avatar/%s" % \
                        hashlib.md5(email_bytes).hexdigest()
                comment['gravatar'] = gravatar_url


def setup(builder):
    before_template_rendered.connect(enhance_template_context)
