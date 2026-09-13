export type Direction = 'ltr' | 'rtl';
export interface ChimeraLocale { id: string; language: string; script: string; direction: Direction }
export function localeFor(id?: string): ChimeraLocale { return id?.toLowerCase().startsWith('ar') ? {id:'ar-SA',language:'ar',script:'Arabic',direction:'rtl'} : {id:'en-US',language:'en',script:'Latin',direction:'ltr'}; }
