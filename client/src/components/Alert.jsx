import React from "react";

export default function Alert({ children, success = false }) {
  return children ? (
    <div
      className={`alert ${success ? "success" : ""}`}
      role={success ? "status" : "alert"}
    >
      {children}
    </div>
  ) : null;
}
