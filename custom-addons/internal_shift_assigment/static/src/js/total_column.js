/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { formatFloat } from "@web/views/fields/formatters";
import { X2Many2DMatrixRenderer } from "@web_widget_x2many_2d_matrix/components/x2many_2d_matrix_renderer/x2many_2d_matrix_renderer.esm";

// Patch the original x2many_2d_matrix renderer
patch(X2Many2DMatrixRenderer.prototype, {
    _aggregateColumn(column) {
        const x = this.columns.findIndex((c) => c.value === column);
        const total = this.matrix
            .map((r) => r[x])
            .map((r) => r.value)
            .reduce((aggr, y) => aggr + y);
        
        if (this.ValueFieldType === "integer") {
            return total;
        }
        
        // Format monetary values properly
        if (this.ValueFieldType === "monetary") {
            return formatFloat(total, { digits: [16, 0] });
        }
        
        return Number(total).toFixed(2);
    },
    
    _aggregateAll() {
        const total = this.matrix
            .map((r) => r.map((x) => x.value).reduce((aggr, x) => aggr + x))
            .reduce((aggr, y) => aggr + y);
            
        if (this.ValueFieldType === "integer") {
            return total;
        }
        
        // Format monetary values properly
        if (this.ValueFieldType === "monetary") {
            return formatFloat(total, { digits: [16, 0] });
        }
        
        return Number(total).toFixed(2);
    }
});
