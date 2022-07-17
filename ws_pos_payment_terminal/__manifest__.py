# -*- coding: utf-8 -*-
{
    "name": "POS Payment Terminal Base",
    "summary": "Base module to add payment terminals in POS",
    "description": """
      This module help to enable payment terminals in odoo to configure with POS.
    """,
    'author': "Wabsol",
    'website': "https://www.wabsol.com/",
    "license": "OPL-1",
    'version': '15.0',
    "depends": [
        "base", "point_of_sale",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],

    "application": True,
    "installable": True,
    "auto_install": False,
}


