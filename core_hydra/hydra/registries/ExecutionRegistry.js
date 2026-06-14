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
/**
 * ExecutionRegistry mirrors the concrete tools registered in src/main.tsx:
 * files, shell, containers, OS automation, media tools and utility packs.
 */
export class ExecutionRegistry {
    getTools() {
        return [
            // Files and workspace search
            tool('read_file', 'Read a workspace file with optional line range.', {
                absolutePath: { type: 'string' },
                startLine: { type: 'number' },
                endLine: { type: 'number' }
            }, ['absolutePath']),
            tool('write_to_file', 'Create or overwrite a workspace file.', {
                absolutePath: { type: 'string' },
                content: { type: 'string' },
                overwrite: { type: 'boolean' }
            }, ['absolutePath', 'content']),
            tool('edit_file', 'Patch an existing file by replacing an exact text block.', {
                absolutePath: { type: 'string' },
                targetContent: { type: 'string' },
                replacementContent: { type: 'string' },
                allowMultiple: { type: 'boolean' }
            }, ['absolutePath', 'targetContent', 'replacementContent']),
            tool('list_dir_glob', 'List files matching a glob pattern.', {
                pattern: { type: 'string' },
                cwd: { type: 'string' }
            }, ['pattern']),
            // Runtime and isolated execution
            tool('run_command', 'Execute a shell command inside the workspace with Tartare safety filtering.', {
                command: { type: 'string' },
                cwd: { type: 'string' },
                timeout: { type: 'number' },
                force_unsafe: { type: 'boolean' }
            }, ['command']),
            tool('python_lab', 'Run Python code in an isolated Docker lab with optional pip requirements.', {
                code: { type: 'string' },
                requirements: { type: 'array', items: { type: 'string' } },
                timeout: { type: 'number' }
            }, ['code']),
            tool('universal_lab', 'Run code in Python, Node, Rust, Go, Bash, C# or C++ inside Docker limits.', {
                language: { type: 'string', enum: ['python', 'node', 'rust', 'go', 'bash', 'csharp', 'cpp'] },
                code: { type: 'string' },
                packages: { type: 'array', items: { type: 'string' } },
                timeout: { type: 'number' }
            }, ['language', 'code']),
            tool('docker', 'Manage Docker containers and images.', {
                action: { type: 'string', enum: ['run', 'exec', 'stop', 'cleanup', 'build', 'ps', 'images', 'pull'] },
                image: { type: 'string' },
                command: { type: 'string' },
                containerName: { type: 'string' },
                dockerfile: { type: 'string' },
                contextDir: { type: 'string' }
            }, ['action']),
            tool('pandora_sandbox', 'Statically analyze suspicious code without executing it.', {
                code: { type: 'string' },
                language: { type: 'string' }
            }, ['code']),
            // Local OS and UI control
            tool('computer_control', 'Control mouse and keyboard for local GUI automation.', {
                action: { type: 'string', enum: ['mouse_move', 'left_click', 'right_click', 'double_click', 'type_text', 'key_press'] },
                x: { type: 'number' },
                y: { type: 'number' },
                text: { type: 'string' },
                keys: { type: 'string' }
            }, ['action']),
            tool('observe_screen', 'Capture or retrieve the latest local screen frame.', {}),
            tool('clipboard', 'Read from or write to the system clipboard.', {
                action: { type: 'string', enum: ['read', 'write'] },
                text: { type: 'string' }
            }, ['action']),
            tool('os_system_health', 'Report CPU, RAM and drive health.', {}),
            tool('os_service_manager', 'List, start, stop or inspect Windows services.', {
                action: { type: 'string', enum: ['list', 'start', 'stop', 'status'] },
                serviceName: { type: 'string' }
            }, ['action']),
            tool('os_process_killer', 'Terminate a local process by PID or name.', {
                pid: { type: 'number' },
                name: { type: 'string' }
            }),
            tool('os_registry_editor', 'Query or edit Windows registry keys with explicit permission.', {
                action: { type: 'string', enum: ['query', 'add', 'delete'] },
                keyPath: { type: 'string' },
                valueName: { type: 'string' },
                data: { type: 'string' }
            }, ['action', 'keyPath']),
            tool('os_cron_manager', 'List, create or delete scheduled tasks.', {
                action: { type: 'string', enum: ['list', 'create', 'delete'] },
                taskName: { type: 'string' },
                command: { type: 'string' },
                schedule: { type: 'string' }
            }, ['action']),
            // Media and creative execution
            tool('blender_3d_render', 'Run a Blender Python script through Docker to render 3D output.', {
                script: { type: 'string' },
                outputName: { type: 'string' }
            }, ['script', 'outputName']),
            tool('media_image_process', 'Resize, convert or grayscale an image.', {
                source: { type: 'string' },
                output: { type: 'string' },
                width: { type: 'number' },
                height: { type: 'number' },
                format: { type: 'string', enum: ['jpeg', 'png', 'webp', 'avif'] },
                grayscale: { type: 'boolean' }
            }, ['source', 'output']),
            tool('media_audio_tags', 'Read or write audio metadata via local media tooling.', {
                filePath: { type: 'string' },
                action: { type: 'string', enum: ['read', 'write'] }
            }, ['filePath']),
            tool('media_video_frame', 'Extract a frame from a video using ffmpeg.', {
                videoPath: { type: 'string' },
                outputPath: { type: 'string' },
                timestamp: { type: 'string' }
            }, ['videoPath', 'outputPath']),
            tool('media_color_palette', 'Extract the dominant color palette from an image.', {
                imagePath: { type: 'string' }
            }, ['imagePath']),
            tool('media_tts_local', 'Speak text or save speech using native OS speech APIs.', {
                text: { type: 'string' },
                outputPath: { type: 'string' }
            }, ['text']),
            // Utility pack
            tool('util_archive_master', 'Create ZIP or TAR archives from a directory.', {
                sourceDir: { type: 'string' },
                outputPath: { type: 'string' },
                format: { type: 'string', enum: ['zip', 'tar'] }
            }, ['sourceDir', 'outputPath']),
            tool('util_qrcode_gen', 'Generate a QR code image from text.', {
                text: { type: 'string' },
                outputPath: { type: 'string' }
            }, ['text', 'outputPath']),
            tool('util_currency_convert', 'Convert currencies through a public exchange-rate API.', {
                amount: { type: 'number' },
                from: { type: 'string' },
                to: { type: 'string' }
            }, ['amount', 'from', 'to']),
            tool('util_unit_convert', 'Convert common physical units.', {
                value: { type: 'number' },
                from: { type: 'string' },
                to: { type: 'string' }
            }, ['value', 'from', 'to']),
            tool('util_password_vault', 'Store or retrieve local encrypted-stub secrets.', {
                key: { type: 'string' },
                value: { type: 'string' },
                masterKey: { type: 'string' }
            }, ['key', 'masterKey'])
        ];
    }
    async execute(name, args) {
        logger.info(`[EXECUTION-REGISTRY] Execution tool accepted: ${name}`);
        return `[EXECUTION] Tool '${name}' accepted by the execution registry. Args: ${JSON.stringify(args)}`;
    }
}
