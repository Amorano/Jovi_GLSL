/**
 * File: util_jov.js
 * Project: Jovi_GLSL
 *
 */

import { app } from "../../scripts/app.js"

export const CONVERTED_TYPE = "converted-widget"

export function widget_get_type(config) {
    // Special handling for COMBO so we restrict links based on the entries
    let type = config?.[0]
    let linkType = type
    if (type instanceof Array) {
      type = 'COMBO'
      linkType = linkType.join(',')
    }
    return { type, linkType }
}

export const widgetFind = (widgets, name) => widgets.find(w => w.name == name);

export function widgetHide(node, widget, suffix = '') {
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

export function widgetShow(widget) {
    if (widget?.origType) {
        widget.type = widget.origType;
        delete widget.origType;
    }

    widget.computeSize = widget.origComputeSize;
    delete widget.origComputeSize;

    if (widget.origSerializeValue) {
        widget.serializeValue = widget.origSerializeValue;
        delete widget.origSerializeValue;
    }

    widget.hidden = false;
    if (widget?.linkedWidgets) {
        for (const w of widget.linkedWidgets) {
            widgetShow(w)
        }
    }
}

export function widgetToWidget(node, widget) {
    widgetShow(widget);
    //const sz = node.size;
    node.removeInput(node.inputs.findIndex((i) => i.widget?.name == widget.name));

    for (const widget of node.widgets) {
        widget.last_y -= LiteGraph.NODE_SLOT_HEIGHT;
    }
    nodeFitHeight(node);
}

export function widgetToInput(node, widget, config) {
    widgetHide(node, widget, "-jov");

    const { linkType } = widget_get_type(config);

    // Add input and store widget config for creating on primitive node
    //const sz = node.size
    node.addInput(widget.name, linkType, {
        widget: { name: widget.name, config },
    })

    for (const widget of node.widgets) {
        widget.last_y += LiteGraph.NODE_SLOT_HEIGHT;
    }
    nodeFitHeight(node);

    // Restore original size but grow if needed
    //node.setSize([Math.max(sz[0], node.size[0]), Math.max(sz[1], node.size[1])])
}

export function nodeFitHeight(node) {
    const size_old = node.size;
    node.computeSize();
    node.setSize([Math.max(size_old[0], node.size[0]), Math.min(size_old[1], node.size[1])]);
    node.setDirtyCanvas(!0, !1);
    app.graph.setDirtyCanvas(!0, !1);
}

function arrayToObject(values, length, parseFn) {
    const result = {};
    for (let i = 0; i < length; i++) {
        result[i] = parseFn(values[i]);
    }
    return result;
}

export function domInnerValueChange(node, pos, widget, value, event=undefined) {
    const type = widget.type.includes("INT") ? Number : parseFloat
    widget.value = arrayToObject(value, Object.keys(value).length, type);
    if (
        widget.options &&
        widget.options.property &&
        node.properties[widget.options.property] !== undefined
        ) {
            node.setProperty(widget.options.property, widget.value)
        }
    if (widget.callback) {

        widget.callback(widget.value, app.canvas, node, pos, event)
    }
}

export function colorHex2RGB(hex) {
  hex = hex.replace(/^#/, '');
  const bigint = parseInt(hex, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return [r, g, b];
}

/*
* Parse a string "255,255,255,255" or a List[255,255,255,255] into hex
*/
export function colorRGB2Hex(input) {
    const rgbArray = typeof input == 'string' ? input.match(/\d+/g) : input;
    if (rgbArray.length < 3) {
        throw new Error('input not 3 or 4 values');
    }
    const hexValues = rgbArray.map((value, index) => {
        if (index == 3 && !value) return 'ff';
        const hex = parseInt(value).toString(16);
        return hex.length == 1 ? '0' + hex : hex;
    });
    return '#' + hexValues.slice(0, 3).join('') + (hexValues[3] || '');
}
