export function explainRows(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) {
    return "Truy vấn không trả về dòng kết quả nào.";
  }

  if (rows.length === 1) {
    const parts = Object.entries(rows[0]).map(([key, value]) => `${key} = ${String(value)}`);
    return `Kết quả truy vấn có 1 dòng: ${parts.join(", ")}.`;
  }

  const columns = Object.keys(rows[0]).join(", ");
  return `Kết quả truy vấn trả về ${rows.length} dòng với các cột ${columns}. Các dòng đầu thể hiện những nhóm hoặc bản ghi nổi bật theo điều kiện truy vấn.`;
}
