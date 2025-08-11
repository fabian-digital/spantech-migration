from odoo import _, api, models
from odoo.tools.misc import formatLang


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _convert_to_tax_line_dict(
        self,
        tax_line,
        partner=None,
        currency=None,
        taxes=None,
        tax_tags=None,
        tax_repartition_line=None,
        group_tax=None,
        account=None,
        analytic_distribution=None,
        tax_amount=None,
    ):
        """Convert the current record to a dictionary to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """

        # handle a case, when tax_line is e.g. bank.rec.widget.line
        if hasattr(tax_line, 'move_id'):
            amt_sign = -1 if tax_line.move_id.is_inbound() else 1
        else:
            amt_sign = 1

        return {
            **super()._convert_to_tax_line_dict(
                tax_line,
                partner=partner,
                currency=currency,
                taxes=taxes,
                tax_tags=tax_tags,
                tax_repartition_line=tax_repartition_line,
                group_tax=group_tax,
                account=account,
                analytic_distribution=analytic_distribution,
                tax_amount=tax_amount,
            ),
            'tax_amount_local': amt_sign * tax_line.balance,
        }

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        if not self.env.company.x_use_ti:
            return super()._prepare_tax_totals(base_lines, currency, tax_lines)

        for line in base_lines:
            sign = (line['is_refund'] and line['record'].move_id.is_outbound()) and -1 or 1
            line['price_unit'] *= sign
            line['price_subtotal'] *= sign

        result = super()._prepare_tax_totals(base_lines, currency, tax_lines)

        # lang_env = self.with_context(lang=partner.lang).env
        to_process = []
        for base_line in base_lines:
            to_update_vals, tax_values_list = self._compute_taxes_for_single_line(base_line)
            to_process.append((base_line, to_update_vals, tax_values_list))

        def grouping_key_generator(_base_line, tax_values):
            source_tax = tax_values['tax_repartition_line'].tax_id
            return {'tax_group': source_tax.tax_group_id}

        global_tax_details = self._aggregate_taxes(to_process, grouping_key_generator=grouping_key_generator)

        tax_group_vals_list = []
        for tax_detail in global_tax_details['tax_details'].values():
            tax_group_vals = {
                'tax_group': tax_detail['tax_group'],
                'base_amount_local': tax_detail['base_amount'],
                'tax_amount_local': tax_detail['tax_amount'],
                'tax_amount_currency': tax_detail['tax_amount_currency'],
                'x_total_amount_currency': tax_detail['base_amount_currency'] + tax_detail['tax_amount_currency'],
            }

            # Handle a manual edition of tax lines.
            if tax_lines is not None:
                matched_tax_lines = [
                    x
                    for x in tax_lines
                    if (x['group_tax'] or x['tax_repartition_line'].tax_id).tax_group_id == tax_detail['tax_group']
                ]
                if matched_tax_lines:
                    tax_group_vals['tax_amount_local'] = sum(x['tax_amount_local'] for x in matched_tax_lines)
                    tax_group_vals['tax_amount_currency'] = sum(x['tax_amount'] for x in matched_tax_lines)

            tax_group_vals_list.append(tax_group_vals)

        amount_untaxed_local = 0.0
        amount_tax_local = 0.0
        amount_tax = 0.0

        for tax_group_vals in sorted(tax_group_vals_list, key=lambda x: (x['tax_group'].sequence, x['tax_group'].id)):
            tax_group = tax_group_vals['tax_group']

            # find title as translations may be misleading
            for _group_title, _group_list in result['groups_by_subtotal'].items():
                for _group in _group_list:
                    if _group['group_key'] == tax_group_vals['tax_group'].id:
                        subtotal_title = _group_title
                        break
                else:
                    continue
                break
            else:
                # fallback to standard method
                subtotal_title = tax_group.preceding_subtotal or _('Untaxed Amount')

            amount_untaxed_local += tax_group_vals['base_amount_local']
            amount_tax_local += tax_group_vals['tax_amount_local']
            amount_tax += tax_group_vals['tax_amount_currency']

            groups_by_subtotal = None

            for _group in result['groups_by_subtotal'][subtotal_title]:
                if _group['tax_group_id'] == tax_group.id:
                    groups_by_subtotal = _group

            if not groups_by_subtotal:
                continue

            assert groups_by_subtotal is not None, f'response is missing tax group {tax_group}'

            groups_by_subtotal.update(
                {
                    'x_tax_group_amount_local': tax_group_vals['tax_amount_local'],
                    'x_tax_group_base_amount_local': tax_group_vals['base_amount_local'],
                    'x_formatted_tax_group_amount_local': formatLang(
                        self.env, tax_group_vals['tax_amount_local'], currency_obj=self.env.company.currency_id
                    ),
                    'x_formatted_tax_group_base_amount_local': formatLang(
                        self.env, tax_group_vals['base_amount_local'], currency_obj=self.env.company.currency_id
                    ),
                    'x_tax_group_total_amount': tax_group_vals['x_total_amount_currency'],
                    'x_formatted_tax_group_total_amount': formatLang(
                        self.env, tax_group_vals['x_total_amount_currency'], currency_obj=currency
                    ),
                }
            )

        result.update(
            {
                'x_tax_amount': amount_tax,
                'x_tax_amount_local': amount_tax_local,
                'x_formatted_tax_amount_local': formatLang(
                    self.env, amount_tax_local, currency_obj=self.env.company.currency_id
                ),
            }
        )

        return result
