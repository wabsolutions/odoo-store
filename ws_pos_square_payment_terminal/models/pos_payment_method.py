# coding: utf-8
import json
import logging
import pprint
import random
import requests
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import string
from werkzeug.exceptions import Forbidden
from odoo import fields, models, api, _
_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        """
        Add square payment terminal to terminal selections.
        """
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [
            ('ws_pos_square_payment_terminal', 'Square Payment Terminal')]

    def _get_base_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = ''
        if base_url:
            url = base_url + '/square_webhook'
        return url

    application_id = fields.Char(string='Application ID', copy=False)
    token_key = fields.Char(string="Token Key", copy=False)
    web_hook_url = fields.Char('Web Hook URl', default=_get_base_url, readonly=True, copy=False)
    device_code = fields.Many2one('device.code',  string="Device Code", copy=False)
    location_id = fields.Char(string="Location ID", copy=False)
    device_name = fields.Char(string="Device Name", copy=False)
    account_type = fields.Selection(string="Account Type",
                                    selection=[('sandbox', 'Test Account'), ('live', 'Production Account'), ],
                                    required=False, )
    manual_card_entry = fields.Boolean(string="Manual Card Entry")
    message = fields.Text(readonly=True)

    @api.model
    def create(self, vals):
        res = super(PosPaymentMethod, self).create(vals)
        if not res.device_code and res.use_payment_terminal == 'ws_pos_square_payment_terminal':
            res.message = 'Please add device code by clicking on Generate Device Code Button.'
        return res

    def write(self, values):
        res = super(PosPaymentMethod, self).write(values)
        if values.get('device_code', False):
            self.message = False
        return res

    def check_device_status(self):
        """Test the Square connection to proceed transactions"""

        if not self.device_code:
            data = {'error': True,
                    'status': 'Error',
                    'message': 'Please Generate Device code from POS payment method',
                    }
            return data
        if self.device_code and not self.device_code.device_id:
            data = {'error': True,
                    'status': 'Error',
                    'message': 'Please Generate Device code from POS payment method.',
                    }
            return data
        try:

            # Todo Sandbox is not working at the moment
            if self.account_type == 'sandbox':
                status_url = 'https://connect.squareupsandbox.com/v2/devices/codes/' + str(self.device_code.device_id)
            else:
                status_url = 'https://connect.squareup.com/v2/devices/codes/' + str(self.device_code.device_id)

            header = {
                'Square-Version': '2022-05-12',
                'Authorization': 'Bearer ' + str(self.token_key),
                'Content-Type': 'application/json'
            }

            response = requests.get(status_url, headers=header)

            if response and response.status_code == 200:
                device_code = json.loads(response.content).get('device_code', False)
                if device_code and device_code.get('status') == 'PAIRED':
                    if device_code and device_code.get('device_id', False):
                        _logger.info("***** Device Status is Paired and device_id is {}**** ".format(device_code.get('device_id')))
                        data = {'error': False,
                                'status': 'PAIRED',
                                'device_id': device_code.get('device_id')
                                }
                        return data
                    else:
                        data = {'error': True,
                                'status': 'Error',
                                'message': "You can't test terminal with sandbox account. "
                                           "Use production credential to test it."}

                elif device_code and device_code.get('status') == 'UNPAIRED':
                    _logger.info("***** Device Status is UnPaired**** ")
                    data = {'error': False,
                            'status': 'unpaired',
                            'message': 'Please check your device either it is connected or not.'}
                    return data
                else:
                    _logger.info("***** Device Status is {}**** ".format(device_code.get('status')))
                    data = {'error': False,
                            'status': device_code.get('status'),
                            'message': 'The Device code has {}. Please generate New code from POS Payment Method and connect your device'.format(device_code.get('status'))}
                    return data

            else:
                _logger.error('*******Square: {}****'.format(json.loads(response.content if response else 'Please check device status from Square')))
                data = {'error': True,
                        'status': 'Error',
                        'message': '{}'.format(json.loads(response.content if response else 'Please check device status from Square')),
                        }
                return data

        except Exception as ex:
            data = {'error': True,
                    'status': 'Error',
                    'message': ex,
                    }
            _logger.error('****** Square:'+str(ex)+'******')
            return data

    def action_generate_device_code(self):
        """
        Generate the Device Code Here
        """
        if not self.device_name:
            raise ValidationError('Device name missing.'
                                  ' Please provide a valid device name.')
        if not self.token_key:
            raise ValidationError('Token key missing.'
                                  ' Please provide a valid token key.')
        if not self.location_id:
            raise ValidationError('Location ID missing.'
                                  ' Please provide a valid location ID.')

        if self.account_type == 'sandbox':
            device_code_url = 'https://connect.squareupsandbox.com/v2/devices/codes'
        else:
            device_code_url = 'https://connect.squareup.com/v2/devices/codes'

        header = {
            'Square-Version': '2022-05-12',
            'Authorization': 'Bearer ' + str(self.token_key),
            'Content-Type': 'application/json'
        }

        body = {
            "idempotency_key": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
            "device_code": {
                "name": self.device_name,
                "product_type": "TERMINAL_API",
                "location_id": self.location_id
            }
        }

        response = requests.post(device_code_url, headers=header, data=json.dumps(body))
        if response and response.status_code == 200:
            device_code = json.loads(response.content).get('device_code', False)
            if device_code:
                device_record = self.env['device.code'].search([('device_id', '=', device_code.get('id'))], limit=1)
                if not device_record:
                    device_record = self.env['device.code'].create({
                        'name': device_code.get('code'),
                        'device_id': device_code.get('id'),
                        'device_code': device_code.get('code'),
                        'product_type': device_code.get('product_type'),
                        'location_id': device_code.get('location_id'),
                        'paired_at': datetime.strptime(device_code.get('pair_by'), '%Y-%m-%dT%H:%M:%S.%fZ').strftime(
                            '%Y-%m-%d %H:%M:%S') if device_code.get('pair_by') else None,
                        'status_change_date': datetime.strptime(device_code.get('status_change_at'),
                                                                '%Y-%m-%dT%H:%M:%S.%fZ').strftime(
                            '%Y-%m-%d %H:%M:%S') if device_code.get('status_change_at') else None,
                        'status': str.lower(device_code.get('status'))
                    })

                self.device_code = device_record.id
                message = f'Please enter this device code <b>[{device_record.name}]</b> within 5 minutes on your ' \
                          f'terminal device to process the transaction.'
                view_id = self.env.ref(
                    'ws_pos_square_payment_terminal.response_message_wizard_form').id
                if view_id:
                    value = {
                        'name': _('Response'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'response.message.wizard',
                        'view_id': False,
                        'context': {'default_message': message},
                        'views': [(view_id, 'form')],
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                    }
                    return value

    def request_for_payment(self, amount, currency, device_id):
        try:

            if self.account_type == 'sandbox':
                checkout_url = 'https://connect.squareupsandbox.com/v2/terminals/checkouts'
                _logger.info("***** Account Type is Sandbox for payment request **** ")
            else:
                checkout_url = 'https://connect.squareup.com/v2/terminals/checkouts'
                _logger.info("***** Account Type is Live for payment request **** ")

            header = {
                'Square-Version': '2022-05-12',
                'Authorization': 'Bearer ' + str(self.token_key),
                'Content-Type': 'application/json'
            }
            body = {
                "idempotency_key": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
                "checkout": {
                    "amount_money": {
                        "amount": int(amount),
                        "currency": currency
                    },
                    "reference_id": "odoo square terminal",
                    "note": "Square payment request from odoo through terminal",
                    # "payment_type": "MANUAL_CARD_ENTRY",
                    "device_options": {
                        "skip_receipt_screen": True,
                        "device_id": device_id
                    }
                }
            }
            if self.manual_card_entry:
                body['checkout'].update({'payment_type': 'MANUAL_CARD_ENTRY'})

            response = requests.post(checkout_url, headers=header, data=json.dumps(body))
            _logger.info("***** Payment Request Response : {} ***** ".format( json.loads(response.content.decode('utf-8')) ))

            if response and response.status_code == 200:
                _logger.info('Inside the status 200')
                checkout = json.loads(response.content.decode('utf-8')).get('checkout')
                _logger.info("***** Payment request : {} **** ".format(checkout))
                if checkout:
                    data = {
                        'error': False,
                        'checkout_id':checkout.get('id'),
                        'status':checkout.get('status'),
                    }
                    return data

            else:
                if response.content:
                    content = json.loads(response.content.decode('utf-8'))
                    _logger.info("***** Payment Request Response ERROR : {} **** ".format(content.get('errors')[0].get('detail')))
                    if content.get('errors'):

                        data = {'error': True,
                            'status': 'Error',
                            'message':content.get('errors')[0].get('detail')
                            }
                    else:
                        _logger.info("***** Payment Request Response ERROR : {} **** ".format(
                            content.get('errors')[0].get('detail')))
                else:
                    _logger.info("***** Payment Request Response ERROR : {} **** ".format(response.content if response else response))
                    data = {'error': True,
                            'status': 'Error',
                            'message':response.content if response else response
                            }

                return data

        except Exception as ex:
            data = {'error': True,
                    'status': 'Error',
                    'message': ex,
                    }
            return data

    def check_payment_status(self,checkout_id):
        try:

            if self.account_type == 'sandbox':
                checkout_url = 'https://connect.squareupsandbox.com/v2/terminals/checkouts/'+str(checkout_id)
            else:
                checkout_url = 'https://connect.squareup.com/v2/terminals/checkouts/'+str(checkout_id)

            header = {
                'Square-Version': '2022-05-12',
                'Authorization': 'Bearer ' + str(self.token_key),
                'Content-Type': 'application/json'
            }

            response = requests.get(checkout_url, headers=header)
            _logger.info('Payment Status Response: {}'.format(json.loads(response.content.decode('utf-8'))))

            if response and response.status_code == 200:
                _logger.info(' Inside 200  Payment Status Response: {}'.format(json.loads(response.content.decode('utf-8'))))
                checkout = json.loads(response.content.decode('utf-8')).get('checkout')
                if checkout:
                    data = {
                        'error': False,
                        'checkout_id': checkout.get('id'),
                        'status': checkout.get('status'),
                    }
                    return data
            else:
                _logger.info(' Error:'.format(json.loads(response.content.decode('utf-8'))))
                content = json.loads(response.content.decode('utf-8'))
                if content.get('errors'):
                    data = {'error': True,
                            'status': 'Error',
                            'message': content.get('errors')[0].get('detail')
                            }
                    return data

        except Exception as ex:
            _logger.info("error*******"+str(ex))
            data = {'error': True,
                    'status': 'Error',
                    'message': ex,
                    }
            return data

    def cancel_payment(self, payment_id):
        try:

            if self.account_type == 'sandbox':
                checkout_url = 'https://connect.squareupsandbox.com/v2/terminals/checkouts/{}/cancel'.format(payment_id)
            else:
                checkout_url = 'https://connect.squareup.com/v2/terminals/checkouts/{}/cancel'.format(payment_id)

            header = {
                'Square-Version': '2022-05-12',
                'Authorization': 'Bearer ' + str(self.token_key),
                'Content-Type': 'application/json'
            }

            response = requests.post(checkout_url, headers=header)

            if response and response.status_code == 200:
                checkout = json.loads(response.content).get('checkout')
                if checkout and checkout.get('status'):
                    data = {
                        'error': False,
                        'checkout_id': checkout.get('id'),
                        'message': 'Payment Transaction has cancelled!',
                    }

            else:
                content = json.loads(response.content)
                if content.get('errors'):
                    data = {'error': True,
                            'status': content.get('id'),
                            'message': 'The transaction status is in {}, so it could not cancel'.format(content.get('status'))
                            }
                    return data

        except Exception as ex:
            data = {'error': True,
                    'status': 'Error',
                    'message': ex,
                    }
            return data

    def square_refund_payment(self,payment_id,amount,currency):
        try:

            if self.account_type == 'sandbox':
                checkout_url = 'https://connect.squareupsandbox.com/v2/refunds'
            else:
                checkout_url = 'https://connect.squareup.com/v2/refunds'

            header = {
                'Square-Version': '2022-05-12',
                'Authorization': 'Bearer ' + str(self.token_key),
                'Content-Type': 'application/json'
            }

            body = {
                "idempotency_key": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
                "amount_money": {
                    "amount": amount,
                    "currency": currency,
                },

                "payment_id": payment_id,
                "reason": "cancel from Odoo"
            }

            response = requests.post(checkout_url, headers=header, data= json.dumps(body))

            if response and response.status_code == 200:
                refund = json.loads(response.content).get('refund')
                if refund and refund.get('status'):
                    data = {
                        'error': False,
                        'refund_id': refund.get('id'),
                        'message': 'Successfully refund the Payment',
                    }

            else:
                content = json.loads(response.content)
                if content.get('errors'):
                    data = {'error': True,
                            'status': 'Error',
                            'message': '{} , So the refund transaction could not process.'.format(
                                content.get('errors')[0].get('code') if content.get('errors') else {} )
                            }
                    return data

        except Exception as ex:
            data = {'error': True,
                    'status': 'Error',
                    'message': ex,
                    }
            return data


class PosPayment(models.Model):
    _inherit = "pos.payment"

    refunded_id = fields.Char(string="Square Refunded ID", required=False, )


class PosOrder(models.Model):
    """Inherit to Populate the refunded_Id value from JS"""
    _inherit = "pos.order"

    def _payment_fields(self, order, ui_paymentline):
        rec = super(PosOrder, self)._payment_fields( order, ui_paymentline)
        rec['refunded_id'] = ui_paymentline.get('refunded_id',False)

        return rec




