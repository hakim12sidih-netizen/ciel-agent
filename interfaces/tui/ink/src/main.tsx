import React from 'react';
import { render } from 'ink';
import App from './App';
import { gateway } from './gateway/client';
import { initEventBus } from './gateway/events';

const { waitUntilExit } = render(<App />);

// Handle cleanup
process.on('SIGINT', async () => {
  await gateway.disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await gateway.disconnect();
  process.exit(0);
});

// Auto-connect gateway
(async () => {
  try {
    const pythonPath = process.env.CIEL_PYTHON || 'python3';
    const cwd = process.env.CIEL_CWD || process.cwd();
    await gateway.connect(pythonPath, cwd);
    initEventBus();
  } catch (err) {
    console.error('Failed to connect to CIEL gateway:', (err as Error).message);
    process.exit(1);
  }
})();

await waitUntilExit();
