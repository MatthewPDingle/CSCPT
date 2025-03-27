import { renderHook, act } from '@testing-library/react-hooks';
import { useWebSocket } from './useWebSocket';

// Mock the WebSocket
class MockWebSocket {
  url: string;
  readyState: number = 0;
  onopen: ((event: any) => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onclose: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  send(data: any) {
    // Mock implementation
  }

  close() {
    // Mock implementation
  }
}

// Mock the global WebSocket object
global.WebSocket = MockWebSocket as any;

describe('useWebSocket', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should initialize with connecting status', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
    expect(result.current.status).toBe('connecting');
  });

  it('should update status to open when connection is established', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
    
    // Simulate WebSocket connection open
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.readyState = WebSocket.OPEN;
      ws.onopen?.({} as Event);
    });
    
    expect(result.current.status).toBe('open');
  });

  it('should handle messages', () => {
    const onMessage = jest.fn();
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { onMessage })
    );
    
    // Simulate receiving a message
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onmessage?.({ data: '{"type":"test"}' } as MessageEvent);
    });
    
    expect(onMessage).toHaveBeenCalled();
    expect(result.current.lastMessage).not.toBeNull();
  });

  it('should handle closing connection', () => {
    const onClose = jest.fn();
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { onClose })
    );
    
    // Simulate connection closing
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onclose?.({ code: 1000 } as CloseEvent);
    });
    
    expect(onClose).toHaveBeenCalled();
    expect(result.current.status).toBe('closed');
  });

  it('should handle errors', () => {
    const onError = jest.fn();
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { onError })
    );
    
    // Simulate an error
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onerror?.({} as Event);
    });
    
    expect(onError).toHaveBeenCalled();
    expect(result.current.status).toBe('error');
  });

  it('should send messages', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
    
    // Mock the send method
    const mockSend = jest.fn();
    const ws = (global as any).WebSocket.mock.instances[0];
    ws.send = mockSend;
    ws.readyState = WebSocket.OPEN;
    
    // Send a message
    act(() => {
      result.current.sendMessage({ type: 'test' });
    });
    
    expect(mockSend).toHaveBeenCalledWith('{"type":"test"}');
  });

  it('should reconnect on connection close if shouldReconnect is true', () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { 
        shouldReconnect: true,
        reconnectInterval: 1000,
        reconnectAttempts: 3
      })
    );
    
    // Simulate connection closing
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onclose?.({ code: 1000 } as CloseEvent);
    });
    
    // Fast-forward timer to trigger reconnect
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    // A new WebSocket should have been created for reconnection
    expect(global.WebSocket).toHaveBeenCalledTimes(2);
  });

  it('should not reconnect if shouldReconnect is false', () => {
    const { result } = renderHook(() => 
      useWebSocket('ws://localhost:8000/ws', { shouldReconnect: false })
    );
    
    // Simulate connection closing
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onclose?.({ code: 1000 } as CloseEvent);
    });
    
    // Fast-forward timer
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // No reconnection should have been attempted
    expect(global.WebSocket).toHaveBeenCalledTimes(1);
  });

  it('should manually reconnect when reconnect method is called', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
    
    // Call reconnect method
    act(() => {
      result.current.reconnect();
    });
    
    // A new WebSocket should have been created
    expect(global.WebSocket).toHaveBeenCalledTimes(2);
  });
});