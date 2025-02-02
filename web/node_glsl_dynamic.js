/**
 * File: node_glsl_dynamic.js
 * Project: Jovi_GLSL
 *
 */

import { app } from "../../scripts/app.js";
import { widgetFind, widgetHide } from './util_jov.js'

const _id = "GLSL DYNAMIC (JOV_GL)";

app.registerExtension({
    name: 'jovi_glsl.node.' + _id,
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!nodeData.name.endsWith("(JOV_GL)")) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = async function () {
            const me = onNodeCreated?.apply(this);
            const widget_fragment = widgetFind(this.widgets, 'FRAGMENT');
            widget_fragment.options.menu = false;
            widgetHide(this, widget_fragment);
            return me;
        }
    }
});
