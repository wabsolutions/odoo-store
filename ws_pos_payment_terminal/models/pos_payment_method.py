# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pos_name = fields.Char('Name for POS', help="Fill in this field If you want to show different name on payment Screen")
