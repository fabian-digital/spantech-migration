from odoo import api, fields, models


class JPKTSettings(models.Model):
    _name = 'jpk.settings'
    _description = 'JPK Settings'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    endpoint_url = fields.Char(string='API Endpoint URL', required=True)
    gate_type = fields.Selection(
        selection=[('eDocuments', 'e-Documents'), ('eDeclarations', 'e-Declarations')],
        default='eDocuments',
        string='API Gate Type',
        required=True,
    )

    jpk_min_filename_length = fields.Integer(default=5, required=True)
    jpk_max_filename_length = fields.Integer(default=55, required=True)
    jpk_encryption_file_key_size = fields.Integer(default=32, required=True)
    jpk_encryption_file_iv_size = fields.Integer(default=16, required=True)
    jpk_encryption_file_block_size = fields.Integer(default=16, required=True)
    jpk_max_chunk_size = fields.Integer(default=60 * 1024 * 1024, required=True)

    jpk_mf_public_key_id = fields.Many2one('ir.attachment')
    jpk_mf_public_key_id_datas = fields.Binary(
        related='jpk_mf_public_key_id.datas', readonly=False, string='JPK MF Public Key'
    )
    jpk_mf_public_key_id_name = fields.Char(
        related='jpk_mf_public_key_id.name', readonly=False, string='JPK MF Public Key Filename'
    )

    @api.onchange('jpk_mf_public_key_id_datas')
    def create_attachment(self):
        if not self.jpk_mf_public_key_id and self.jpk_mf_public_key_id_datas:
            self.jpk_mf_public_key_id = (
                self.env['ir.attachment']
                .create({'name': self.jpk_mf_public_key_id_name, 'datas': self.jpk_mf_public_key_id_datas})
                .id
            )

    def name_get(self):
        return [(_rec.id, f'{_rec.name} - {_rec.gate_type}') for _rec in self]
