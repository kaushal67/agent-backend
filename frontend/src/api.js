const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function parseJsonOrText(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return { detail: text };
}

export async function askTriageQuestion(message) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ msg: message })
  });

  if (!response.ok) {
    const payload = await parseJsonOrText(response);
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function askTriageImage(file, note) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("note", note || "");

  const response = await fetch(`${API_BASE_URL}/ask/image`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const payload = await parseJsonOrText(response);
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchQueryHistory(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/queries?limit=${limit}`);

  if (!response.ok) {
    const payload = await parseJsonOrText(response);
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}
