###################################################################################
#
#    Conéctika.Tech
#    Copyright (C) 2023-TODAY Conéctika.Tech (<http://conectika.tech>).
#
#    Author: Jericho Ruz
#
###################################################################################

{
    'name': 'Enterprise Account Invoice Downloader',
    'summary': 'Account Invoice CFDI (XML and PDF) Downloader and SAT PDF validations EDI MX',
    'version': '16.0.1',
    'author': 'Conectika.tech',
    'website': "https://conectika.tech",
    'company': 'Conectika.tech',
    'maintainer': 'Conectika.tech',
    'live_test_url': 'https://conectika.tech',
    "category": "Industries",
    "depends" : ["l10n_mx_edi",],
    'data': [
        'security/ir.model.access.csv',
        'data/res_partner_data.xml',
        'wizard/cfdi_downloader_view.xml',
        'views/partner_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
}
