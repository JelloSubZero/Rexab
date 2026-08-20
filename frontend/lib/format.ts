export function formatMoney(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  return `${sign}${Math.abs(amount).toFixed(2)} zł`;
}

export function formatSignedMoney(amount: number): string {
  const sign = amount > 0 ? "+" : amount < 0 ? "-" : "";
  return `${sign}${Math.abs(amount).toFixed(2)} zł`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
