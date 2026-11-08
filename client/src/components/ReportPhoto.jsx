import React, { useRef, useState } from "react";

export default function ReportPhoto({ src, title }) {
  const [failed, setFailed] = useState(false);
  const dialog = useRef(null);
  if (failed)
    return (
      <p className="muted">
        Photo unavailable. The rest of your report is still available.
      </p>
    );
  return (
    <section className="report-photo">
      <h3>Photo</h3>
      <button
        className="photo-open"
        onClick={() => dialog.current.showModal()}
        aria-label="Enlarge report photo"
      >
        <img
          src={src}
          alt={`Photo for ${title}`}
          onError={() => setFailed(true)}
        />
      </button>
      <small>Select the photo to enlarge it.</small>
      <dialog ref={dialog} className="photo-dialog">
        <button onClick={() => dialog.current.close()} autoFocus>
          Close photo
        </button>
        <img
          src={src}
          alt={`Enlarged photo for ${title}`}
          onError={() => {
            dialog.current?.close();
            setFailed(true);
          }}
        />
      </dialog>
    </section>
  );
}
