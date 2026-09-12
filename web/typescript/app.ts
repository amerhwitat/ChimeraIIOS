export interface RuntimeState { edition:string; registerBits:number; ipcSamples:number }
export const initialState:RuntimeState={edition:'computer',registerBits:8192,ipcSamples:0};
export function recordIpcSample(state:RuntimeState):RuntimeState{return {...state,ipcSamples:state.ipcSamples+1};}
