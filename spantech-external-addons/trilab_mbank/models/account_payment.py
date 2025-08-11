from odoo import api, models

MBANK_CODES = ['mbank_payment', 'mbank_split_payment']


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _get_method_codes_using_bank_account(self):
        return super(AccountPayment, self)._get_method_codes_using_bank_account() + MBANK_CODES

    @api.model
    def _get_method_codes_needing_bank_account(self):
        return super(AccountPayment, self)._get_method_codes_needing_bank_account() + MBANK_CODES


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        # noinspection PyProtectedMember
        res = super(AccountPaymentMethod, self)._get_payment_method_information()
        res.update(
            {
                'mbank_payment': {'mode': 'multi', 'domain': [('type', '=', 'bank')]},
                'mbank_split_payment': {'mode': 'multi', 'domain': [('type', '=', 'bank')]},
            }
        )
        return res
