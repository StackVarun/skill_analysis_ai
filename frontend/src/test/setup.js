import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Node may already expose an unavailable localStorage global. Use the actual
// jsdom browser storage explicitly, since Vitest 3 preserves existing globals.
for (const name of ['localStorage', 'sessionStorage']) {
  Object.defineProperty(globalThis, name, {
    configurable: true,
    enumerable: true,
    writable: true,
    value: globalThis.jsdom.window[name],
  });
}

afterEach(() => {
  cleanup();
  localStorage.clear();
  sessionStorage.clear();
});
