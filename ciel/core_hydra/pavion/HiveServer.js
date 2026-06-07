import { WebSocketServer } from 'ws';
import logger from '../../utils/logger.js';
/**
 * HIVE SERVER — Le Nid Mère de HYDRA
 * Gère une flotte de Reverse WebSockets (Pavions).
 * Permet à l'IA d'interagir à distance via une seule API interne.
 */
export class HiveServer {
    port;
    wss = null;
    pavions = new Map();
    pendingRequests = new Map();
    constructor(port = 8089) {
        this.port = port;
    }
    start() {
        this.wss = new WebSocketServer({ port: this.port });
        logger.info(`[HIVE] 🕸️ Hive Server listening on port ${this.port}. Waiting for Pavions to connect...`);
        this.wss.on('connection', (ws, req) => {
            const ip = req.socket.remoteAddress || 'unknown';
            let pavionId = `pav_${Date.now()}`;
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message.toString());
                    // Initial Handshake
                    if (data.type === 'handshake') {
                        pavionId = data.id || pavionId;
                        this.pavions.set(pavionId, {
                            id: pavionId,
                            ws: ws,
                            hostname: data.hostname,
                            os: data.os,
                            ip: ip,
                            status: 'active',
                            connectedAt: Date.now()
                        });
                        logger.info(`[HIVE] 🪲 Pavion Connected: ${data.hostname} (${ip}) -> ID: ${pavionId}`);
                        // Acknowledge
                        ws.send(JSON.stringify({ type: 'handshake_ok' }));
                    }
                    // Command response
                    if (data.type === 'response' && data.requestId) {
                        const reqHandler = this.pendingRequests.get(data.requestId);
                        if (reqHandler) {
                            reqHandler.resolve(data.output);
                            this.pendingRequests.delete(data.requestId);
                        }
                    }
                }
                catch (e) {
                    logger.error(`[HIVE] Invalid message from Pavion: ${e}`);
                }
            });
            ws.on('close', () => {
                logger.warn(`[HIVE] 🥀 Pavion Disconnected: ${pavionId}`);
                const p = this.pavions.get(pavionId);
                if (p) {
                    p.status = 'dead';
                    this.pavions.set(pavionId, p); // keep in log but mark dead
                }
            });
        });
    }
    getPavions() {
        return Array.from(this.pavions.values()).map(p => ({
            id: p.id,
            hostname: p.hostname,
            ip: p.ip,
            status: p.status
        }));
    }
    async sendCommand(pavionId, command) {
        const p = this.pavions.get(pavionId);
        if (!p || p.status !== 'active') {
            throw new Error("Pavion offline or not found.");
        }
        const reqId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
        return new Promise((resolve, reject) => {
            // Timeout after 60s
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(reqId);
                reject(new Error("Pavion response timeout"));
            }, 60000);
            this.pendingRequests.set(reqId, {
                resolve: (data) => {
                    clearTimeout(timeout);
                    resolve(data);
                },
                reject: (err) => {
                    clearTimeout(timeout);
                    reject(err);
                }
            });
            p.ws.send(JSON.stringify({
                type: 'exec',
                requestId: reqId,
                command: command
            }));
        });
    }
}
// Singleton export
export const hiveServer = new HiveServer();
