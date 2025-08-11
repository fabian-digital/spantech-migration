from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _x_prepare_invoice_line(self, line_list=False, **optional_values):
        self.ensure_one()
        quantity = self.qty_to_invoice
        if self.is_downpayment and line_list and quantity < 0:
            sum_field = 'price_total' if self.tax_id.price_include else 'price_subtotal'
            invoice_line_ids = line_list.filtered(
                lambda line_id: not line_id.is_downpayment and line_id.tax_id.ids == self.tax_id.ids
            )
            so_line_ids = self.order_id.order_line.filtered(
                lambda line_id: not line_id.is_downpayment and line_id.tax_id.ids == self.tax_id.ids
            )
            invoice_value = sum(
                line_id.qty_to_invoice * (line_id[sum_field] / line_id.product_uom_qty) for line_id in invoice_line_ids
            )
            so_value = sum(line_id[sum_field] for line_id in so_line_ids)
            quantity = -1 * (invoice_value / so_value)
        res = self._prepare_invoice_line(sequence=optional_values['sequence'])
        res['quantity'] = quantity

        return res

    def _prepare_invoice_line(self, **optional_values):
        is_advance = self._context.get('x_advance', False)

        if is_advance and 'name' in optional_values:
            del optional_values['name']

        line_data = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        if self.env.context.get('x_convert_rate'):
            currency_rate = self.env['res.currency.rate'].browse(self.env.context.get('x_convert_rate'))
            if currency_rate:
                line_data['price_unit'] *= currency_rate.inverse_company_rate

        return line_data

    def _compute_untaxed_amount_to_invoice(self):
        super()._compute_untaxed_amount_to_invoice()

        # ref #5016, handle edge case, when issuing down payment for sale order in draft state
        # temporarily change line state to done, recalc untaxed amount and then bring original status back
        for line_id in self.filtered(lambda rec: rec.is_downpayment and rec.state not in ('sale', 'done')):
            _tmp_state = line_id.state
            line_id.write({'state': 'done'})
            super(SaleOrderLine, line_id)._compute_untaxed_amount_to_invoice()
            line_id.write({'state': _tmp_state})
