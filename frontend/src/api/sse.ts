export interface SSEMessage {
  event: string;
  data: string;
}

/**
 * Incrementally parses a Server-Sent Events byte stream.
 * Handles CRLF, multi-line `data:` fields, comments and chunks split mid-message.
 */
export async function* parseSSE(stream: ReadableStream<Uint8Array>): AsyncGenerator<SSEMessage> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const parseBlock = (block: string): SSEMessage | null => {
    let event = 'message';
    const data: string[] = [];
    for (const line of block.split('\n')) {
      if (!line || line.startsWith(':')) continue;
      const idx = line.indexOf(':');
      const field = idx === -1 ? line : line.slice(0, idx);
      const value = idx === -1 ? '' : line.slice(idx + 1).replace(/^ /, '');
      if (field === 'event') event = value;
      else if (field === 'data') data.push(value);
    }
    return data.length ? { event, data: data.join('\n') } : null;
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n?/g, '\n');

      let sep: number;
      while ((sep = buffer.indexOf('\n\n')) !== -1) {
        const msg = parseBlock(buffer.slice(0, sep));
        buffer = buffer.slice(sep + 2);
        if (msg) yield msg;
      }
      if (done) break;
    }
    const tail = parseBlock(buffer);
    if (tail) yield tail;
  } finally {
    reader.releaseLock();
  }
}
