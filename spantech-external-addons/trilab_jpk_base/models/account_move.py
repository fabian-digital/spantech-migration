from odoo import _, api, fields, models

MPP_EDGE_AMOUNT = 15_000.00

X_PL_VAT_OUT_TYPES = [
    ('RO', 'dokument zbiorczy wewnętrzny zawierający sprzedaż z kas rejestrujących'),
    ('FP', 'faktura do paragonu, o której mowa w art. 109 ust. 3d ustawy'),
    ('WEW', 'dokument wewnętrzny'),
]

X_PL_VAT_IN_TYPES = [
    ('MK', 'metoda kasowa'),
    ('VAT_RR', 'faktury VAT RR, o której mowa w art. 116 ustawy'),
    ('WEW', 'dokument wewnętrzny'),
]


class AccountMove(models.Model):
    _inherit = 'account.move'

    pl_vat_date = fields.Date(string='VAT Date', index=True)

    x_pl_vat_typ_dokumentu = fields.Selection(
        string='Typ Dokumentu',
        selection=X_PL_VAT_OUT_TYPES,
        readonly=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        help='Oznaczenia dowodu sprzedaży',
    )

    x_pl_vat_dokument_zakupu = fields.Selection(
        string='Dokument Zakupu', selection=X_PL_VAT_IN_TYPES, help='Oznaczenie dowodu zakupu'
    )

    x_pl_vat_mpp = fields.Boolean(
        string='MPP',
        default=False,
        tracking=True,
        help='Transakcja objęta obowiązkiem stosowania mechanizmu podzielonej płatności. '
        'Oznaczenie MPP należy stosować do faktur o kwocie brutto wyższej '
        'niż 15 000,00 zł, które dokumentują dostawę towarów lub świadczenie usług '
        'wymienionych w załączniku nr 15 do ustawy.',
    )

    # sprzedaż
    x_pl_vat_sw = fields.Boolean(
        string='SW',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Dostawa w ramach sprzedaży wysyłkowej z terytorium kraju, ' 'o której mowa w art. 23 ustawy',
    )
    x_pl_vat_ee = fields.Boolean(
        string='EE',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Świadczenie usług telekomunikacyjnych, nadawczych i elektronicznych, ' 'o których mowa w art. 28k ustawy',
    )
    x_pl_vat_tp = fields.Boolean(
        string='TP',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Istniejące powiązania między nabywcą a dokonującym dostawy towarów lub '
        'usługodawcą, o których mowa w art. 32 ust. 2 pkt 1 ustawy.',
    )
    x_pl_vat_tt_wnt = fields.Boolean(
        string='TT-WNT',
        default=False,
        help='Wewnątrzwspólnotowe nabycie towarów dokonane przez drugiego w kolejności '
        'podatnika VAT w ramach transakcji trójstronnej w procedurze uproszczonej, '
        'o której mowa w dziale XII rozdział 8 ustawy.',
    )
    x_pl_vat_tt_d = fields.Boolean(
        string='TT-D',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Dostawa towarów poza terytorium kraju dokonana przez drugiego w kolejności '
        'podatnika VAT w ramach transakcji trójstronnej w procedurze uproszczonej, '
        'o której mowa w dziale XII rozdział 8 ustawy.',
    )
    x_pl_vat_mr_t = fields.Boolean(
        string='MR-T',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Świadczenie usług turystyki opodatkowane na zasadach marży ' 'zgodnie z art. 119 ustawy.',
    )
    x_pl_vat_mr_uz = fields.Boolean(
        string='MR-UZ',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Dostawa towarów używanych, dzieł sztuki, przedmiotów kolekcjonerskich '
        'i antyków, opodatkowana na zasadach marży zgodnie z art. 120 ustawy.',
    )
    x_pl_vat_i42 = fields.Boolean(
        string='I42',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Wewnątrzwspólnotowa dostawa towarów następująca po imporcie tych towarów '
        'w ramach procedury celnej 42 (import).',
    )
    x_pl_vat_i63 = fields.Boolean(
        string='I63',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Wewnątrzwspólnotowa dostawa towarów następująca po imporcie tych towarów '
        'w ramach procedury celnej 63 (import).',
    )
    x_pl_vat_b_spv = fields.Boolean(
        string='B-SPV',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Transfer bonu jednego przeznaczenia dokonany przez podatnika działającego '
        'we własnym imieniu, opodatkowany zgodnie z art. 8a ust. 1 ustawy.',
    )
    x_pl_vat_b_spv_dostawa = fields.Boolean(
        string='B-SPV Dostawa',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Dostawa towarów oraz świadczenie usług, których dotyczy bon jednego '
        'przeznaczenia na rzecz podatnika, który wyemitował bon zgodnie '
        'z art. 8a ust. 4 ustawy.',
    )
    x_pl_vat_b_mpv_prowizja = fields.Boolean(
        string='B-MPV Prowizja',
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Świadczenie usług pośrednictwa oraz innych usług dotyczących '
        'transferu bonu różnego przeznaczenia, opodatkowane zgodnie '
        'z art. 8b ust. 2 ustawy.',
    )
    x_pl_vat_korekta_podstawy_opodt = fields.Boolean(
        string='Korekta Podstawy Opodatkowania',
        default=False,
        readonly=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        help='Korekta podstawy opodatkowania oraz podatku należnego, ' 'o której mowa w art. 89a ust. 1 i 4 ustawy',
    )
    x_pl_vat_reverse_charge = fields.Boolean(
        string='Reverse charge', default=False, readonly=True, tracking=True, states={'draft': [('readonly', False)]}
    )

    x_pl_vat_wsto_ee = fields.Boolean(string='WSTO_EE', readonly=True, states={'draft': [('readonly', False)]})
    x_pl_vat_ied = fields.Boolean(string='IED', readonly=True, states={'draft': [('readonly', False)]})
    x_pl_change_jpk_proof = fields.Char(string='Change JPK Proof Document')

    # zakup
    x_pl_vat_imp = fields.Boolean(
        string='IMP',
        default=False,
        help='Oznaczenie dotyczące podatku naliczonego z tytułu importu towarów, '
        'w tym importu towarów rozliczanego zgodnie z art. 33a ustawy.',
    )

    def _x_assign_mpp(self):
        base_pl_id = self.env.ref('base.pl')
        pln_currency_id = self.env.ref('base.PLN')

        # noinspection PyUnboundLocalVariable
        for move_id in self.filtered(
            lambda m_id: m_id.move_type == 'out_invoice'
            and not m_id.x_pl_vat_mpp
            and m_id.partner_id.is_company
            and (partner_vat := m_id.partner_id.vat)
            and (m_id.partner_id.country_id == base_pl_id or partner_vat[:2] == 'PL')
            and any(m_id.invoice_line_ids.product_id.product_tmpl_id.mapped('x_pl_vat_mpp'))
            and m_id.currency_id.compare_amounts(
                m_id.currency_id._convert(
                    m_id.amount_total,
                    pln_currency_id,
                    m_id.company_id,
                    m_id.invoice_date or m_id.date or fields.Date.context_today(m_id),
                ),
                MPP_EDGE_AMOUNT,
            )
            >= 0
        ):
            move_id.x_pl_vat_mpp = True
            move_id.message_post(body=_('The invoice was marked with the split payment mechanism'))

    def action_post(self):
        response = super().action_post()

        self._x_assign_mpp()

        for move_id in self.filtered(lambda m_id: m_id.is_invoice(include_receipts=True) and not m_id.pl_vat_date):
            if (
                move_id.invoice_date
                and move_id.is_sale_document(include_receipts=True)
                and hasattr(move_id, 'x_invoice_sale_date')
            ):
                date = move_id.x_invoice_sale_date
            else:
                date = move_id.date

            move_id.pl_vat_date = date

        return response

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.x_pl_vat_tp = self.partner_id.x_pl_vat_tp if self.partner_id else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            default_type = vals.get('move_type', self._context.get('default_move_type'))
            if 'x_pl_vat_tp' not in vals and default_type in self.get_sale_types() and vals.get('partner_id'):
                vals['x_pl_vat_tp'] = self.env['res.partner'].browse(vals['partner_id']).x_pl_vat_tp

        return super().create(vals_list)
