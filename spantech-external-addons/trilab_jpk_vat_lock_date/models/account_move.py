from odoo import _, api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('pl_vat_date')
    def _onchange_pl_vat_date(self):
        if self.pl_vat_date and self.company_id.x_jpk_lock_date and self.pl_vat_date <= self.company_id.x_jpk_lock_date:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _(
                        'The TAX date falls within a period closed for TAX reporting, '
                        'there will be a potential need to correct the reports.'
                    ),
                }
            }

    def action_post(self):
        if self.env.company.x_use_ti and self._context.get('x_check_jpk_lock_date', True):
            for invoice_id in self:
                if not invoice_id.is_invoice(include_receipts=True):
                    continue

                jpk_date = (
                    invoice_id.pl_vat_date
                    or (invoice_id.move_type in ('out_invoice', 'out_refund') and invoice_id.x_invoice_sale_date)
                    or invoice_id.date
                )

                if (
                    invoice_id.company_id.x_jpk_lock_date
                    and jpk_date
                    and jpk_date <= invoice_id.company_id.x_jpk_lock_date
                ):
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'jpk.vat.date_exception',
                        'name': 'Warning',
                        'view_mode': 'form',
                        'target': 'new',
                    }

            # noinspection PyUnusedLocal
            self = self.with_context(x_check_jpk_lock_date=False)

        return super().action_post()
