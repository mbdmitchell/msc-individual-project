const fs = require('fs');
const config = require('../../config.json');

// const { DAWN_NODE_PATH } = config;
const DAWN_NODE_PATH = config['DAWN_NODE_PATH'];

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

    // Create a buffer on the GPU
    const inputBuffer = device.createBuffer({
        label: 'input buffer',
        size: input.byteLength,
        usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST,
    });

    device.queue.writeBuffer(inputBuffer, 0, input); // Copy our input data to that buffer

    const outputBuffer = device.createBuffer({
        label: 'work buffer',
        size: 512, // 4 * 128 (i32 size * max no_of_elem)
        usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST,
    });

    // Set up a bindGroup to tell the shader which buffers to use for the computation
    const bindGroup = device.createBindGroup({
        label: 'bindGroup for work buffer',
        layout: pipeline.getBindGroupLayout(0),
        entries: [
            { binding: 0, resource: { buffer: inputBuffer } },
            { binding: 1, resource: { buffer: outputBuffer } },
        ],
    });

    // Encode commands to do the computation
    const encoder = device.createCommandEncoder({
        label: 'control flow encoder',
    });
    const pass = encoder.beginComputePass({
        label: 'control flow compute pass',
    });
    pass.setPipeline(pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.dispatchWorkgroups(input.length);
    pass.end();

    const resultBuffer = device.createBuffer({
        label: 'output buffer',
        size: 512, // 4 * 128 (i32 size * max no_of_elem)
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

    console.log(result);

}

shaderPath = process.argv[2]
input = new Uint32Array(JSON.parse(process.argv[3]))


test(shaderPath, input).catch(console.error);