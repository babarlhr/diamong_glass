# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Manufacturing Extension',
    'version': '1.0',
    'summary': 'Manufacturing Extension',
    'description': """
          Manufacturing Extension
    """,
    'company': "ERPIFY",
    'author': "ERPIFY",
    'maintainer': "ERPIFY",
    'website': "http://www.odoo.ie",
    'category': 'Manufacturing',

    'depends': ['mrp'],
    'data': [
        'views/templates.xml',
    ],
    'css': [
    ],
    'demo': [],
    'application': False,
    'installable': True,
    'auto_install': False,
    'qweb': [],
}
