export type ThamudicGlyph = { glyph: string; codepoint?: string; translit?: string; confidence?: number; note?: string };
export type ThamudicResearchRecord = {
  id: string; createdAt: string; order: string; imageName?: string;
  glyphs: ThamudicGlyph[]; transliteration: string; translation?: string; sourceUrls: string[];
};
export type ThamudicSearchResult = {
  title: string; url: string; thumbnail?: string; source: string; license?: string; description?: string; author?: string;
};
export interface ThamudicNlpBridge {
  search(query: string, limit?: number): Promise<{results: ThamudicSearchResult[]}>;
  crawl(sources: ThamudicSearchResult[]): Promise<{results: ThamudicSearchResult[]}>;
  train(config: {model: string; epochs: number; batch: number; lr: number}): Promise<Record<string, unknown>>;
  predict(boxes: ThamudicGlyph[], order: string): Promise<{glyphs: ThamudicGlyph[]; transliteration: string; translation?: string}>;
  evaluate(): Promise<Record<string, unknown>>;
}
