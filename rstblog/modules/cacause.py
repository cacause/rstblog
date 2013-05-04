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
from rstblog.signals import before_file_built
from StringIO import StringIO
import jinja2

cacause_context = {}


def get_article_id(source_filename):
    m = hashlib.md5()
    m.update(source_filename)
    return m.hexdigest()


def get_comment_meta(comment_file):
    headers = ['---']
    f = open(comment_file, 'r')
    for line in f:
        line = line.rstrip()
        if not line:
            break
        headers.append(line)

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
    print "### cacause context"
    print cacause_context


def process_blog_entry(context):
    # create cacause context is empty
    if not 'comments' in cacause_context:
        template_context = context.get_default_template_context()
        cacause_dir = template_context['config'].get('cacause_dir')
        if not cacause_dir:
            print "cacause: can't find cacause_dir in config.yml"
            sys.exit(1)
        read_comments("/".join([context.builder.project_folder, cacause_dir]))


@jinja2.contextfunction
def get_cacause(context):
    print "###### JINJA CACAUSE ###"
    print cacause_context
    print context

    article_id = get_article_id(context['source_filename'])
    count = 0
    if article_id in cacause_context['comments']:
        count = len(cacause_context['comments'][article_id])
    print "%d comment(s)" % count

    # TODO: insert existing comments here

    # TODO insert comment creation form here
    cacause_txt="""
<div id="cacause_thread">
<p>insert %d existing comment(s) here<p>
<p>insert creation comment form here</p>
</div>
""" % count

    return jinja2.Markup(cacause_txt.encode('utf-8'))

def setup(builder):
    before_file_built.connect(process_blog_entry)
    builder.jinja_env.globals['get_cacause'] = get_cacause
