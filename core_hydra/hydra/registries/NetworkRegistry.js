import logger from '../../../utils/logger.js';
function tool(name, description, properties = {}, required = []) {
    return {
        type: 'function',
        function: {
            name,
            description,
            parameters: { type: 'object', properties, required }
        }
    };
}
export class NetworkRegistry {
    getTools() {
        return [
            tool('scout_network', 'Analyze the local network inventory and trusted lab devices.', { target_ip: { type: 'string' } }),
            tool('broadcast_telegram', 'Send a status report through the configured Telegram bridge.', { message: { type: 'string' } }, ['message']),
            tool('n8n_manager', 'Trigger n8n webhooks or inspect configured n8n workflows.', {
                webhookUrl: { type: 'string' },
                payload: { type: 'object' },
                method: { type: 'string', enum: ['GET', 'POST', 'PUT'] },
                action: { type: 'string', enum: ['list_workflows', 'get_execution', 'activate_workflow'] },
                workflowId: { type: 'string' },
                executionId: { type: 'string' }
            }),
            // Web and knowledge acquisition
            tool('web_search', 'Search the web and return ranked results.', {
                query: { type: 'string' },
                limit: { type: 'number' }
            }, ['query']),
            tool('web_fetch', 'Fetch readable text from a URL.', {
                url: { type: 'string' }
            }, ['url']),
            tool('crawler_swarm', 'Crawl and index a domain into Hydra knowledge storage.', {
                domain: { type: 'string' },
                maxDepth: { type: 'number' },
                targetTopic: { type: 'string' }
            }, ['domain', 'targetTopic']),
            tool('web_sitemap_crawler', 'Extract links and sitemap-like structure from a website.', {
                url: { type: 'string' }
            }, ['url']),
            tool('web_link_checker', 'Check a web page for links and broken-link analysis.', {
                url: { type: 'string' }
            }, ['url']),
            tool('web_adblock_scout', 'Detect trackers and ad scripts on a page.', {
                url: { type: 'string' }
            }, ['url']),
            tool('web_social_scraper', 'Extract public profile metadata from supported social platforms.', {
                platform: { type: 'string', enum: ['twitter', 'github', 'linkedin'] },
                username: { type: 'string' }
            }, ['platform', 'username']),
            tool('web_ip_origin', 'Analyze public origin data for an IP address.', {
                ip: { type: 'string' }
            }, ['ip']),
            // Authorized cyber/intel pack
            tool('cyber_port_scan', 'Scan ports on an authorized host or local lab target.', {
                host: { type: 'string' },
                ports: { type: 'array', items: { type: 'number' } }
            }, ['host']),
            tool('cyber_dns_lookup', 'Resolve DNS records for a domain.', {
                domain: { type: 'string' }
            }, ['domain']),
            tool('cyber_whois', 'Retrieve WHOIS data for a domain or IP.', {
                domain: { type: 'string' }
            }, ['domain']),
            tool('cyber_ip_tracker', 'Geolocate and inspect public IP metadata.', {
                ip: { type: 'string' }
            }, ['ip']),
            tool('cyber_metadata_cleaner', 'Inspect file metadata and recommend cleaning steps.', {
                filePath: { type: 'string' }
            }, ['filePath']),
            tool('intel_cve_lookup', 'Search public CVE data for a product or keyword.', {
                query: { type: 'string' }
            }, ['query']),
            tool('intel_sqlite_explorer', 'Run a SQL query against a local SQLite database.', {
                dbPath: { type: 'string' },
                sql: { type: 'string' }
            }, ['dbPath', 'sql']),
            tool('intel_json_optimizer', 'Validate, minify or pretty-print JSON.', {
                rawJson: { type: 'string' },
                format: { type: 'string', enum: ['minify', 'beautify'] }
            }, ['rawJson']),
            tool('intel_sentiment_analysis', 'Analyze text sentiment locally.', {
                text: { type: 'string' }
            }, ['text']),
            tool('intel_causal_correlation', 'Compute correlation between two numerical arrays.', {
                dataA: { type: 'array', items: { type: 'number' } },
                dataB: { type: 'array', items: { type: 'number' } }
            }, ['dataA', 'dataB'])
        ];
    }
    async execute(name, args) {
        logger.info(`[NETWORK-REGISTRY] Network/intel tool accepted: ${name}`);
        return `[NETWORK] Tool '${name}' accepted by the network registry. Args: ${JSON.stringify(args)}`;
    }
}
