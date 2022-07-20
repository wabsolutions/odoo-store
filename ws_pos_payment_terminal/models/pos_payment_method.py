# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_ws_pos_square_payment_terminal = fields.Boolean(string="Square Payment Terminal")


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pos_name = fields.Char('Name for POS', help="Fill in this field If you want to show different name on payment Screen")
