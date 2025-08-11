from odoo import api, fields, models


class JpkMagReportWizard(models.TransientModel):
    _name = 'jpk.mag.report.wizard'
    _description = 'JPK MAG Report Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company', default=lambda self: self.env.company.id, required=True, string='Company'
    )

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)

    is_jpk_transfer_installed = fields.Boolean(compute='_compute_jpk_transfer')

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        required=True,
        default=lambda self: self._default_warehouse_id(),
        check_company=True,
    )

    @api.depends('company_id')
    def _compute_jpk_transfer(self):
        for rec in self:
            rec.is_jpk_transfer_installed = rec.company_id.x_is_jpk_transfer_installed()

    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

    def _export(self, report_type):
        """Default export is PDF."""
        self.ensure_one()
        return self._print_report(report_type)

    def _prepare_report_data(self):
        self.ensure_one()
        return {
            'wizard_id': self.id,
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'warehouse_id': self.warehouse_id.id,
            'lang': self.env.ref('base.lang_pl').code,
        }

    def _print_report(self, report_type):
        self.ensure_one()

        report_name = 'trilab_jpk_mag.jpk_mag_report'
        data = self._prepare_report_data()

        if report_type == 'jpk_transfer':
            # noinspection PyUnresolvedReferences
            return self.env[f'report.{report_name}'].transfer_xml(data)

        return (
            self.env['ir.actions.report']
            .search(domain=[('report_name', '=', report_name), ('report_type', '=', report_type)], limit=1)
            .report_action([], data=data)
        )

    def button_export_html(self):
        return self._export(report_type='qweb-html')

    def button_export_xlsx(self):
        return self._export(report_type='jpk_xlsx')

    def button_export_xml(self):
        return self._export(report_type='jpk_xml')

    def button_transfer_xml(self):
        return self._export(report_type='jpk_transfer')
