# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID


class ResponseMessage(models.TransientModel):
    _name = 'response.message.wizard'
    _description = 'Custom Response Message'

    message = fields.Html("Response", readonly=True)
