# -*- coding: utf-8 -*-
{
    'name': 'POS Square Payment Terminal',
    'summary': 'Integrate your POS with Square payment terminal',
    'description': 'Integrate your POS with Square payment terminal',

    'author': "Wabsol",
    'website': "https://www.wabsol.com/",
    "license": "OPL-1",
    'version': '15.0',
    'category': 'Sales/Point of Sale',
    'depends': ['ws_pos_payment_terminal'],

    'data': [
        'security/ir.model.access.csv',

        'views/pos_payment_method_views.xml',
        'views/device_code_views.xml',

        'wizard/response_message_view.xml',
    ],

    'assets': {
        'point_of_sale.assets': [
            'ws_pos_square_payment_terminal/static/**/*',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,
}
