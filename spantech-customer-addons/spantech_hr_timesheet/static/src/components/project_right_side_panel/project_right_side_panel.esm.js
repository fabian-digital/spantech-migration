/* @odoo-module */

import {ProjectRightSidePanel} from "@project/components/project_right_side_panel/project_right_side_panel";
import {patch} from "@web/core/utils/patch";

patch(
    ProjectRightSidePanel.prototype,
    "@spantech_hr_timesheet/components/project_right_side_panel/project_right_side_panel",
    {
        async loadPerformance() {
            const performance = await this.orm.call(
                "project.project",
                "get_performance_items",
                [[this.projectId]],
                {context: this.context}
            );
            this.state.data.performance_items = performance;
            return performance;
        },
    }
);
