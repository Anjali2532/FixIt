import React from "react";

export const categories = [
  "Lighting",
  "Roads & Sidewalks",
  "Trash & Recycling",
  "Plumbing",
  "Equipment & Facilities",
  "Safety",
  "Other",
];
export const statuses = ["Reported", "In Progress", "Resolved"];
export const date = (value) =>
  new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
export function Message({ children }) {
  return (
    children && (
      <div className="alert" role="alert">
        {children}
      </div>
    )
  );
}
export function Badge({ status }) {
  return (
    <span
      className={`report-badge ${status.toLowerCase().replaceAll(" ", "-")}`}
    >
      {status}
    </span>
  );
}
