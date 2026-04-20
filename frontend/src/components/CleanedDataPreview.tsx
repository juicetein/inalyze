import { formatCurrency } from "../lib/format";
import type { CleanedDataset } from "../types";

interface CleanedDataPreviewProps {
  cleanedDataset: CleanedDataset;
}

export function CleanedDataPreview({ cleanedDataset }: CleanedDataPreviewProps) {
  const rows = cleanedDataset.rows.slice(0, 8);
  const emptyValue = "-";

  return (
    <section className="panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Cleaned Data Preview</p>
          <h2>See how the rows were standardized</h2>
          <p className="section-helper">
            This preview shows the cleaned output that powers the analytics and insight engine.
          </p>
        </div>
        <span className="pill pill-neutral">Showing first {rows.length} rows</span>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Product</th>
              <th>Quantity</th>
              <th>Total</th>
              <th>Date</th>
              <th>Fulfillment</th>
              <th>Payment</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.row_number}>
                <td>{row.order_id ?? emptyValue}</td>
                <td>{row.customer_identifier ?? emptyValue}</td>
                <td>{row.product_name ?? emptyValue}</td>
                <td>{row.quantity ?? emptyValue}</td>
                <td>{typeof row.order_total === "number" ? formatCurrency(row.order_total) : emptyValue}</td>
                <td>{row.order_date ?? emptyValue}</td>
                <td>{row.fulfillment_status}</td>
                <td>{row.payment_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
