###################################################################################
#
#    Conéctika.Tech
#    Copyright (C) 2023-TODAY Conéctika.Tech (<http://conectika.tech>).
#
#    Author: Jericho Ruz
#
###################################################################################

{
    'name': 'Community Account Invoice Downloader',
    'summary': 'Account Invoice Attachments Downloader for Community versions no EDI',
    'version': '16.0.1',
    'author': 'Conectika.tech',
    'website': "https://conectika.tech",
    'company': 'Conectika.tech',
    'maintainer': 'Conectika.tech',
    'live_test_url': 'https://conectika.tech',
    "category": "Industries",
    "depends" : ["account",],
    'data': [
        'security/ir.model.access.csv',
        'data/res_partner_data.xml',
        'wizard/cfdi_downloader_view.xml',
        'views/partner_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
