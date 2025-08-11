from odoo import api, fields, models
from odoo.tools import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_is_corrected_line = fields.Boolean(default=False)

    # only for user input/visualization
    x_quantity = fields.Float(compute='_x_compute_reverse', digits='Product Unit of Measure', readonly=False)
    x_price_subtotal = fields.Float(compute='_x_compute_reverse', store=False, readonly=True)
    x_price_total = fields.Float(compute='_x_compute_reverse', store=False, readonly=True)
    x_force_print = fields.Boolean('Force Print')

    @api.depends_context('x_show_as_before')
    @api.depends('quantity', 'price_unit', 'price_subtotal', 'price_total')
    def _x_compute_reverse(self):
        for line_id in self:
            sign = -1

            if self._context.get('x_show_as_before'):
                sign *= -1

            line_id.x_quantity = sign * line_id.quantity
            line_id.x_price_subtotal = sign * line_id.price_subtotal
            line_id.x_price_total = sign * line_id.price_total

    @api.onchange('x_quantity', 'x_price_subtotal', 'x_price_total')
    def x_set_reverse_values(self):
        for line_id in self:
            line_id.quantity = -line_id.x_quantity
            line_id.price_subtotal = -line_id.x_price_subtotal
            line_id.price_total = -line_id.x_price_total

    def _convert_to_tax_line_dict(self):
        result = super()._convert_to_tax_line_dict()

        if self.move_id.x_use_ti:
            sign = self.move_id.move_type in ('out_refund',) and -1 or 1
            result['tax_amount'] *= sign
            result['tax_amount_local'] *= sign

        return result

    @api.depends('currency_id', 'company_id', 'move_id.date', 'move_id.x_currency_rate', 'move_id.x_invoice_sale_date')
    def _compute_currency_rate(self):
        super()._compute_currency_rate()

        for line_id in self.filtered(
            lambda rec: rec.move_id.x_use_ti
            and rec.move_id.x_show_currency_rate
            and rec.move_id.currency_id
            and not rec.move_id.currency_id.is_zero(rec.move_id.x_currency_rate)
            and rec.currency_id == rec.move_id.currency_id
        ):
            line_id.currency_rate = 1 / line_id.move_id.x_currency_rate

    def _stock_account_get_anglo_saxon_price_unit(self):
        # from stock_account
        # noinspection PyUnresolvedReferences
        price_unit = super()._stock_account_get_anglo_saxon_price_unit()

        # Fix of Odoo bug, applied to Polish companies' Credit Notes.
        # The first level of parent method has been used here as a fix (stock_account/models/account_move.py)
        if not self.move_id.x_use_ti or not self.sale_line_ids:
            return price_unit

        if not self.product_id:
            return self.price_unit

        account_move_id = self.move_id.reversed_entry_id

        # find original account.move for SO with already posted invoice and refund
        if not account_move_id and (
            (
                so_posted_move_ids := (self.sale_line_ids.invoice_lines - self).move_id.filtered(
                    lambda m_id: m_id.state == 'posted'
                )
            )
            and so_posted_move_ids.filtered(lambda m_id: m_id.move_type == 'out_refund')
            and (invoice_move_ids := so_posted_move_ids.filtered(lambda m_id: m_id.move_type == 'out_invoice'))
        ):
            account_move_id = fields.first(invoice_move_ids)

        original_line_id = self.env['account.move.line']
        while not original_line_id and account_move_id:
            original_line_id = fields.first(
                account_move_id.line_ids.filtered(
                    lambda l_id: l_id.display_type == 'cogs'
                    and l_id.product_id == self.product_id
                    and l_id.product_uom_id == self.product_uom_id
                    and l_id.currency_id.compare_amounts(l_id.price_unit, 0.0) >= 0
                )
            )
            account_move_id = account_move_id.reversed_entry_id

        return original_line_id.price_unit if original_line_id else price_unit

    def _eligible_for_cogs(self):
        # noinspection PyUnresolvedReferences
        res = super()._eligible_for_cogs()

        if (
            not res
            or self.move_type != 'out_refund'
            or not self.move_id.x_use_ti
            or not self._context.get('x_ti_additional_checks_eligible_for_cogs')
        ):
            return res

        # for matching invoice line from another site (x_is_corrected_line)
        # sum quantity of this line and self.quantity and check if it is zero
        return not float_is_zero(
            sum(
                self.move_id.invoice_line_ids.filtered(
                    lambda _l_id: _l_id.x_is_corrected_line is (not self.x_is_corrected_line)
                    and _l_id.product_id == self.product_id
                    and _l_id.product_uom_id == self.product_uom_id
                ).mapped('quantity')
            )
            + self.quantity,
            precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure'),
        )

    def x_can_print(self):
        self.ensure_one()

        if not self.move_id.x_use_ti or not self.company_id.x_hide_zero_price_aml:
            return True

        return (
            self.x_force_print
            or self.display_type in ('line_section', 'line_note')
            or not self.currency_id.is_zero(self.price_unit)
        )

    def x_get_net_price_unit(self, before_discount=False):
        self.ensure_one()

        # handle precision, even if UOM is not set
        if self.product_uom_id:
            rounding = self.product_uom_id.rounding
        else:
            rounding = 1 / 10 ** self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if float_is_zero(self.quantity, precision_rounding=rounding):
            return 0.0

        line_record = self._convert_to_tax_base_line_dict()

        # workaround on rounding in taxes.compute_all, later it is multiplied
        line_record['quantity'] /= rounding

        if before_discount:
            line_record['discount'] = 0.0

        summary, tax_values_list = self.env['account.tax']._compute_taxes_for_single_line(line_record)

        # do not round here
        return summary['price_subtotal'] / self.quantity * rounding

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.company.x_use_ti:
            return super().create(vals_list)

        if self.env.context.get('x_ti_default_balance'):
            for vals in vals_list:
                vals.setdefault('balance')

        return super().create(vals_list)
