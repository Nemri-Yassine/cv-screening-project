const CITATION = /\[([\w-]+\.pdf)\]/g;

/** Unique PDF citations in the order they first appear in the answer. */
export function citationOrder(answer: string): string[] {
  const seen = new Set<string>();
  const order: string[] = [];
  for (const match of answer.matchAll(CITATION)) {
    const fileName = match[1];
    if (!seen.has(fileName)) {
      seen.add(fileName);
      order.push(fileName);
    }
  }
  return order;
}

/** 1-based index of a file in the answer, or null if not cited. */
export function citationIndex(answer: string, fileName: string): number | null {
  const index = citationOrder(answer).indexOf(fileName);
  return index === -1 ? null : index + 1;
}
