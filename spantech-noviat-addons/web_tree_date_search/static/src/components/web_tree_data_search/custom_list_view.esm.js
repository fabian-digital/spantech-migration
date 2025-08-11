/** @odoo-module */
const {useState, onPatched} = owl;
import {ListController} from "@web/views/list/list_controller";
import {patch} from "@web/core/utils/patch";
import rpc from "web.rpc";

patch(
    ListController.prototype,
    "web_tree_date_search/static/src/components/web_tree_data_search/custom_list_view.js",
    {
        setup() {
            var self = this;
            this._super.apply(this, arguments);
            this.dateFilters = [];
            this.state = useState({
                date_search_domain: [],
            });
            rpc.query({
                model: "ir.config_parameter",
                method: "get_web_tree_date_search_parameters",
            }).then(function (data) {
                var parameter_applicability =
                    data["web_tree_date_search.applicability"];
                if (
                    self.props.context.dates_filter !== undefined ||
                    parameter_applicability === "all"
                ) {
                    self.date_search_domain = [];
                    self.dateFilters = [];
                    if (["all", "selective"].includes(parameter_applicability)) {
                        self._build_date_filters(parameter_applicability);
                    }
                }
            });
            onPatched(() => {
                this.handleComponentPatched();
            });
        },
        _build_date_filters(parameter_applicability) {
            var self = this;
            var dateFilterBool = false;
            var dateFilterArray = [];
            if ("context" in self.props && "dates_filter" in self.props.context) {
                if (Array.isArray(self.props.context.dates_filter)) {
                    if (self.props.context.dates_filter.length > 0) {
                        dateFilterBool = true;
                        dateFilterArray = self.props.context.dates_filter;
                    }
                } else if (typeof self.props.context.dates_filter === "boolean") {
                    dateFilterBool = self.props.context.dates_filter;
                } else if (typeof self.props.context.dates_filter === "number") {
                    dateFilterBool = Boolean(self.props.context.dates_filter);
                }
            } else if (parameter_applicability === "all") {
                dateFilterBool = true;
            }
            var dateFilters = [];
            var fields = [];
            if (dateFilterBool) {
                if (dateFilterArray.length > 0) {
                    dateFilters = self._get_date_filter_list(self, dateFilterArray);
                } else {
                    var all_fields = Object.keys(self.props.fields);
                    var visible_fields = Object.keys(self.model.fieldNodes);
                    all_fields.forEach(function (field_name) {
                        if (visible_fields.includes(field_name)) {
                            fields.push(field_name);
                        }
                    });
                    dateFilters = self._get_date_filter_list(self, fields);
                }
                self.dateFilters = dateFilters;
            }
        },
        async handleComponentPatched() {
            var dts = this.date_search_domain;
            if (dts && dts.length > 0) {
                var is_in = false;
                var pdomains = this.props.domain;
                for (var i = 0; i < pdomains.length; i++) {
                    for (var j = 0; j < dts.length; j++) {
                        if (pdomains[i].toString() === dts[j].toString()) {
                            is_in = true;
                            break;
                        }
                    }
                    if (is_in) {
                        break;
                    }
                }
                if (!is_in) {
                    var list = document.getElementsByClassName("date_search_input");
                    for (var k = 0; k < list.length; k++) {
                        list[k].value = null;
                    }
                }
            }
        },
        _onchange_date_from(ev, dateFilter) {
            var self = this;
            var dts = false;
            if (ev.currentTarget.value !== "") {
                dts = ev.currentTarget.value;
            }
            self._changeValue(dts, dateFilter, "from");
        },
        _onchange_date_to(ev, dateFilter) {
            var self = this;
            var dts = false;
            if (ev.currentTarget.value !== "") {
                dts = ev.currentTarget.value;
            }
            self._changeValue(dts, dateFilter, "to");
        },

        _changeValue(moment, dateFilter, target) {
            var date_search_domain = this.date_search_domain;
            var new_date_search_domain = [];
            if (date_search_domain) {
                _.each(date_search_domain, function (domain_array) {
                    if (
                        domain_array[0] !== dateFilter.name ||
                        (domain_array[0] === dateFilter.name &&
                            ((target === "to" && domain_array[1] !== "<=") ||
                                (target === "from" && domain_array[1] !== ">=")))
                    ) {
                        new_date_search_domain.push(domain_array);
                    }
                });
            }
            if (moment !== false && moment !== undefined) {
                if (target === "to") {
                    new_date_search_domain.push([dateFilter.name, "<=", moment]);
                } else {
                    new_date_search_domain.push([dateFilter.name, ">=", moment]);
                }
            }
            this.date_search_domain = new_date_search_domain;
            if (
                new_date_search_domain === undefined ||
                new_date_search_domain.length === 0
            ) {
                if (
                    this.env.searchModel.domainParts.state.facetLabel === "Date Filters"
                ) {
                    this.env.searchModel.deactivateGroup(
                        this.env.searchModel.domainParts.state.groupId
                    );
                }
            } else {
                this.env.searchModel.setDomainParts({
                    state: {
                        domain: new_date_search_domain,
                        facetLabel: "Date Filters",
                    },
                });
            }
        },
        _get_date_filter_list(self, fields) {
            var dateFilters = [];
            fields.forEach(function (field_name) {
                if (
                    typeof self.props.fields[field_name] !== "undefined" &&
                    ["date", "datetime"].includes(self.props.fields[field_name].type) &&
                    (self.props.fields[field_name].invisible !== "1" ||
                        !self.props.fields[field_name].invisible) &&
                    self.props.fields[field_name].searchable === true
                ) {
                    dateFilters.push({
                        type: self.props.fields[field_name].type,
                        display_name: self.props.fields[field_name].string,
                        name: field_name,
                    });
                }
            });
            return dateFilters;
        },
    }
);
