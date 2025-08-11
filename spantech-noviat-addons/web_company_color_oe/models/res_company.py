# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    SCSS_TEMPLATE = """
        .o_main_navbar {
          background: %(color_navbar_bg)s !important;
          background-color: %(color_navbar_bg)s !important;
          color: %(color_navbar_text)s !important;

          > .o_menu_brand {
            color: %(color_navbar_text)s !important;
            &:hover, &:focus, &:active, &:focus:active {
              background-color: %(color_navbar_bg_hover)s !important;
            }
          }

          .show {
            .dropdown-toggle {
              background-color: %(color_navbar_bg_hover)s !important;
            }
          }

          > ul {
            > li {
              > a, > label {
                color: %(color_navbar_text)s !important;

                &:hover, &:focus, &:active, &:focus:active {
                  background-color: %(color_navbar_bg_hover)s !important;
                }
              }
            }
          }
        }
        a[href],
        a[tabindex],
        .btn-link,
        .o_external_button {
          color: %(color_link_text)s !important;
        }
        a:hover,
        .btn-link:hover {
          color: %(color_link_text_hover)s !important;
        }
        .btn-primary:not(.disabled) {
          color: %(color_button_text)s !important;
          background-color: %(color_button_bg)s !important;
          border-color: %(color_button_bg)s !important;
        }
        .ui-autocomplete .ui-menu-item > a.ui-state-active {
          color: %(color_button_text)s !important;
          border-color: %(color_button_bg)s !important;
        }
        .btn-primary:hover:not(.disabled) {
          color: %(color_button_text)s !important;
          background-color: %(color_button_bg_hover)s !important;
          border-color: %(color_button_bg_hover)s !important;
        }
        .ui-autocomplete .ui-menu-item > a.ui-state-active:hover {
          color: %(color_button_text)s !important;
          border-color: %(color_button_bg_hover)s !important;
        }
        .o_searchview .o_searchview_facet .o_searchview_facet_label {
          color: %(color_button_text)s !important;
          background-color: %(color_button_bg)s !important;
        }
        .o_form_view .o_horizontal_separator {
          color: %(color_link_text)s !important;
        }
        .o_form_view .oe_button_box .oe_stat_button .o_button_icon,
        .o_form_view .oe_button_box .oe_stat_button .o_stat_info .o_stat_value,
        .o_form_view .oe_button_box .oe_stat_button > span .o_stat_value {
          color: %(color_link_text)s !important;
        }
        .o_form_view .o_form_statusbar > .o_statusbar_status >
        .o_arrow_button.btn-primary.disabled {
          color: %(color_link_text)s !important;
        }
    """
