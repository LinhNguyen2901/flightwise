export type TimeCell = readonly [number, number];
export type Selection = {originId: number | null; cells: TimeCell[]; animationHour: number | null; isPlaying: boolean};
export type SelectionAction =
  | {type: 'airport'; originId: number}
  | {type: 'clearAirport'}
  | {type: 'cell'; cell: TimeCell}
  | {type: 'replaceCells'; cells: TimeCell[]}
  | {type: 'clearTime'}
  | {type: 'enterPlayback'; autoPlay?: boolean}
  | {type: 'play'}
  | {type: 'pause'}
  | {type: 'seek'; hour: number}
  | {type: 'tick'}
  | {type: 'exitPlayback'}
  | {type: 'reset'};

export const initialSelection: Selection = {originId: null, cells: [], animationHour: null, isPlaying: false};
const key = ([day, hour]: TimeCell) => `${day}:${hour}`;

export function selectionReducer(state: Selection, action: SelectionAction): Selection {
  switch (action.type) {
    case 'airport': return {...state, originId: state.originId === action.originId ? null : action.originId,
      isPlaying: false};
    case 'clearAirport': return {...state, originId: null, isPlaying: false};
    case 'cell': return {...state, animationHour: null, isPlaying: false,
      cells: state.cells.some(cell => key(cell) === key(action.cell))
      ? state.cells.filter(cell => key(cell) !== key(action.cell)) : [...state.cells, action.cell]};
    case 'replaceCells': return {...state, cells: action.cells, animationHour: null, isPlaying: false};
    case 'clearTime': return {...state, cells: [], animationHour: null, isPlaying: false};
    // The saved pre-review layout omits autoPlay, so it still restores its paused entry.
    case 'enterPlayback': return {...state, animationHour: 0, isPlaying: action.autoPlay ?? false};
    case 'play': return {...state, animationHour: state.animationHour === 23 ? 0 : state.animationHour ?? 0,
      isPlaying: true};
    case 'pause': return {...state, isPlaying: false};
    case 'seek': return {...state, animationHour: Math.max(0, Math.min(23, action.hour)), isPlaying: false};
    case 'tick': return state.isPlaying && state.animationHour !== null
      ? state.animationHour >= 22 ? {...state, animationHour: 23, isPlaying: false}
        : {...state, animationHour: state.animationHour + 1} : state;
    case 'exitPlayback': return {...state, animationHour: null, isPlaying: false};
    case 'reset': return initialSelection;
  }
}
