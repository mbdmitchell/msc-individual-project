// TODO: Move file out of wgsl and rename run_wgsl.js. NB: make sure to update in the other files

const fs = require('fs');
const config = require('../../config.json');

function envToDawnVariantFilePath(env) {

    if (!env || !env.hasOwnProperty("DAWN_VARIANT")) {
        return config["DAWN_NODE_PATH"];
    }

    switch (env["DAWN_VARIANT"]) {
        case 'normal':
            return config["DAWN_NODE_PATH"];
        case 'meta_mutant':
            return config["DAWN_MUTANT_NODE_PATH"];
        case 'mutant_tracking':
            return config["DAWN_MUTANT_TRACKING_NODE_PATH"];
        default:
            throw new Error("Unrecognised DAWN_VARIANT value");
    }
}

const DAWN_NODE_PATH = envToDawnVariantFilePath(process.env);
const { create, globals } = require(DAWN_NODE_PATH);

Object.assign(globalThis, globals); // Provides constants like GPUBufferUsage.MAP_READ
let navigator = { gpu: create([]) };

async function fileExists(filePath) {
    try {
        await fs.promises.access(filePath);
        return true;
    } catch {
        return false;
    }
}

async function test(shaderPath, input){

    try {
        const is_global_array_code_type = input !== null;

        const buffer_size = 2048 // 8 * 256 (i32 size * max no_of_elem)  TODO: Make dependant on size of CFG

        const adapter = await navigator.gpu?.requestAdapter();

        const device = await adapter?.requestDevice();

        if (!device) {
            fail('need a browser that supports WebGPU');
            return;
        }

        if (!fileExists(shaderPath)) {
            throw new Error(`WGSL file not found: ${shaderPath}`);
        }

        const shader = await fs.promises.readFile(shaderPath, 'utf-8');

        const module = device.createShaderModule({
            label: 'control flow compute module',
            code: shader,
        });

        const pipeline = device.createComputePipeline({
            label: 'control flow compute pipeline',
            layout: 'auto',
            compute: {
                module,
            },
        });

        // Create buffers on the GPU only if is_global_array_code_type is true
        let inputBuffer;

        if (is_global_array_code_type) {
            inputBuffer = device.createBuffer({
                label: 'input buffer',
                size: input.byteLength,
                usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST,
            });
            device.queue.writeBuffer(inputBuffer, 0, input); // Copy our input data to that buffer
        }

        const outputBuffer = device.createBuffer({
            label: 'work buffer',
            size: buffer_size,
            usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST,
        });

        // Set up a bindGroup to tell the shader which buffers to use for the computation
        let entries = [
            {binding: 0, resource: {buffer: outputBuffer}},
        ];
        if (is_global_array_code_type) {
            entries.push({binding: 1, resource: {buffer: inputBuffer}})
        }

        const layoutNum = 0

        const bindGroup = device.createBindGroup({
            label: 'bindGroup for work buffer',
            layout: pipeline.getBindGroupLayout(layoutNum),
            entries: entries,
        });

        // Encode commands to do the computation
        const encoder = device.createCommandEncoder({
            label: 'control flow encoder',
        });
        const pass = encoder.beginComputePass({
            label: 'control flow compute pass',
        });
        pass.setPipeline(pipeline);
        pass.setBindGroup(layoutNum, bindGroup);
        pass.dispatchWorkgroups(1);
        pass.end();

        const resultBuffer = device.createBuffer({
            label: 'output buffer',
            size: buffer_size,
            usage: GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST,
        });

        // Encode a command to copy the results to a mappable buffer.
        encoder.copyBufferToBuffer(outputBuffer, 0, resultBuffer, 0, resultBuffer.size);

        // Finish encoding and submit the commands
        const commandBuffer = encoder.finish();
        device.queue.submit([commandBuffer]);

        // Read the results
        await resultBuffer.mapAsync(GPUMapMode.READ);
        const mappedRange = new Int32Array(resultBuffer.getMappedRange());
        const resultArray = Array.from(mappedRange);

        const result = resultArray.slice(0, resultArray.indexOf(0));
        resultBuffer.unmap();
        console.log(JSON.stringify(result, null, 2));  // stringify ensures whole string printed

    } catch (e) {
        console.log(e)
    }

}

shaderPath = process.argv[2]
const input = process.argv[3] ? new Uint32Array(JSON.parse(process.argv[3])) : null;


test(shaderPath, input).catch(console.error);