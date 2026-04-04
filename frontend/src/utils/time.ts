/**
 * API timestamps are stored as UTC in SQLite but lack a timezone suffix.
 * Normalise them so `new Date()` interprets them correctly.
 */
export function utcDate(value: string): Date {
  if (/[Z+-]\d{2}:?\d{2}$/.test(value) || value.endsWith("Z")) {
    return new Date(value);
  }
  return new Date(value.replace(" ", "T") + "Z");
}
