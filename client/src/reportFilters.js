export const defaultFilters = {
  q: "",
  category: "",
  status: "",
  page: 1,
  assignee: "",
  attention: "",
  sort: "newest",
};

export function readReportFilters(params) {
  const filters = { ...defaultFilters };
  for (const key of Object.keys(filters)) {
    if (params.has(key)) filters[key] = params.get(key);
  }
  const page = Number(filters.page);
  filters.page =
    Number.isInteger(page) && page >= 1 && page <= 1000000 ? page : 1;
  return filters;
}

export function writeReportFilters(filters) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(defaultFilters)) {
    if (filters[key] !== value && filters[key] !== "") {
      params.set(key, String(filters[key]));
    }
  }
  return params;
}

export function toggleReportSort(current, column) {
  if (column === "Submitted") return current === "newest" ? "oldest" : "newest";
  const name = column.toLowerCase();
  return current === name ? `${name}-desc` : name;
}
