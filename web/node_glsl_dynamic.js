/**/

import { app } from "../../scripts/app.js";

const _id = "GLSL DYNAMIC (JOV_GL)";

const CONVERTED_TYPE = "converted-widget"

const widgetFind = (widgets, name) => widgets.find(w => w.name == name);

function widgetHide(node, widget, suffix = '') {
    if ((widget?.hidden || false) || widget.type?.startsWith(CONVERTED_TYPE + suffix)) {
        return;
    }
    widget.origType = widget.type;
    widget.type = CONVERTED_TYPE + suffix;
    widget.hidden = true;

    widget.origComputeSize = widget.computeSize;
    widget.computeSize = () => [0, -4];

    widget.origSerializeValue = widget.serializeValue;
    widget.serializeValue = async () => {
        // Prevent serializing the widget if we have no input linked
        if (!node.inputs) {
            return undefined;
        }

        let node_input = node.inputs.find((i) => i.widget?.name == widget.name);
        if (!node_input || !node_input.link) {
            return undefined;
        }
        return widget.origSerializeValue ? widget.origSerializeValue() : widget.value;
    }

    // Hide any linked widgets, e.g. seed+seedControl
    if (widget.linkedWidgets) {
        for (const w of widget.linkedWidgets) {
            widgetHide(node, w, ':' + widget.name);
        }
    }
}

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
