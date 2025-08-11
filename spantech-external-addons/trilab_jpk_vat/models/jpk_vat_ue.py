import base64

from odoo import api, fields, models
from odoo.addons.trilab_jpk_vat.reports.jpk_vat_ue import JpkVatEuReport


class VatEuGroup(models.Model):
    _name = 'jpk.vat.ue.group'
    _description = 'VAT EU Group'

    group = fields.Selection(
        [(k, v['name']) for k, v in JpkVatEuReport.GROUP_MAPPING.items()], string='JPK UE Group', required=True
    )
    country_code = fields.Char(string='Country Code', required=True)
    nip = fields.Char(string='NIP', required=True)
    amount = fields.Float(string='Amount')
    tt = fields.Char(string='Trilateral Transaction')
    vat_ue_id = fields.Many2one('jpk.vat.ue', string='Report', required=True, ondelete='cascade')


class VatEu(models.Model):
    _name = 'jpk.vat.ue'
    _description = 'VAT UE'

    version = fields.Char(string='JPK Version')

    year = fields.Integer(string='Year')
    month = fields.Integer(string='Month')

    cel_zlozenia = fields.Integer(string='Cel złożenia')

    source_xml = fields.Binary()

    group_line_ids = fields.One2many('jpk.vat.ue.group', 'vat_ue_id', string='Group Lines')
    group1_line_ids = fields.One2many('jpk.vat.ue.group', compute='_compute_group_lines', string='Group1 Lines')
    group2_line_ids = fields.One2many('jpk.vat.ue.group', compute='_compute_group_lines', string='Group2 Lines')
    group3_line_ids = fields.One2many('jpk.vat.ue.group', compute='_compute_group_lines', string='Group3 Lines')
    group4_line_ids = fields.One2many('jpk.vat.ue.group', compute='_compute_group_lines', string='Group4 Lines')

    is_jpk_transfer_installed = fields.Boolean(compute='_compute_is_jpk_transfer_installed', readonly=True)

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('group_line_ids')
    def _compute_group_lines(self):
        empty_group = self.env['jpk.vat.ue.group']
        for report_id in self:
            for field in ('group1_line_ids', 'group2_line_ids', 'group3_line_ids', 'group4_line_ids'):
                report_id[field] = empty_group

            for line_id in report_id.group_line_ids:
                report_id[f'{line_id.group}_line_ids'] |= line_id

    # noinspection HttpUrlsUsage
    # noinspection PyUnusedLocal
    def get_xml(self, options=None):
        return base64.b64decode(self.source_xml)

    # noinspection PyUnusedLocal
    def _compute_is_jpk_transfer_installed(self):
        self.is_jpk_transfer_installed = self.env.company.x_is_jpk_transfer_installed()

    def action_generate_xml(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'trilab_jpk_vat.jpk_vat_eu_report',
            'report_type': 'jpk_xml',
            'report_file': 'trilab_jpk_vat.jpk_vat_eu_report',
            'name': 'VAT UE',
            'context': {'active_ids': self.ids},
        }

    def action_transfer_xml(self):
        document_type = 'trilab_jpk_base.vat_ue5_v2_0e_doc_type'

        # noinspection PyUnresolvedReferences
        transfer_id = self.env['jpk.transfer'].create_with_document(
            {
                'name': f'VAT UE {self.month}/{self.year}',
                'jpk_type': 'JPK',
                'file_name': f'vat_ue_{self.month}_{self.year}.xml',
                'reference_document': f'{self._name},{self.id}',
                'data': self.get_xml(),
                'document_type': document_type,
            }
        )

        # noinspection PyUnresolvedReferences
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jpk.transfer',
            'res_id': transfer_id.id,
            'view_mode': 'form',
            # 'target': 'new'
        }

    # noinspection PyMethodMayBeStatic
    def action_cancel(self):
        # self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    def action_generate_pdf(self):
        return self.env.ref('trilab_jpk_vat.report_vat_ue_pdf').report_action(self)

    def get_print_report_name(self):
        return f'vat_ue_{self.month:02d}_{self.year}{self.cel_zlozenia > 1 and "_korekta" or ""}'

    def action_transfer_correction_xml(self):
        document_type = 'trilab_jpk_base.vat_uek5_v2_1e_doc_type'

        # noinspection PyUnresolvedReferences
        transfer_id = self.env['jpk.transfer'].create_with_document(
            {
                'name': f'VAT UEK {self.month}/{self.year}',
                'jpk_type': 'JPK',
                'file_name': f'vat_uek_{self.month}_{self.year}.xml',
                'reference_document': f'{self._name},{self.id}',
                'data': self.get_xml(),
                'document_type': document_type,
            }
        )

        # noinspection PyUnresolvedReferences
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jpk.transfer',
            'views': [[False, 'form']],
            'res_id': transfer_id.id,
            # 'target': 'new'
        }

    def get_transfer_info(self):
        self.ensure_one()

        if not self.is_jpk_transfer_installed:
            return {}

        transfer_id = self.env['jpk.transfer'].search(
            [('reference_document', '=', f'{self._name},{self.id}'), ('confirmation_id', '!=', False)], limit=1
        )

        if not transfer_id:
            return {}

        return {'reference_number': transfer_id.reference_number}
