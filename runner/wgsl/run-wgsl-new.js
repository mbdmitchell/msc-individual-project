const fs = require('fs');
const config = require('../../config.json');

const { DAWN_NODE_PATH } = config;

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

async function main(abs_code_filepath, directions_path){

    const adapter = await navigator.gpu?.requestAdapter();
    const device = await adapter?.requestDevice();

    if (!device) {
        fail('need a browser that supports WebGPU');
        return;
    }

    const shaderPath = abs_code_filepath;
    const directionPath = directions_path;

    const [shaderFileExists, directionFileExists] = await Promise.all([
        fileExists(shaderPath),
        fileExists(directionPath)
    ]);

    if (!shaderFileExists) {
        throw new Error(`WGSL file not found: ${shaderPath}`);
    }

    if (!directionFileExists) {
        throw new Error(`Direction file not found: ${directionPath}`);
    }

    const [directionsData, shader] = await Promise.all([
        fs.promises.readFile(directionPath, 'utf-8'),
        fs.promises.readFile(shaderPath, 'utf-8'),
    ]);

    const bufferValues = JSON.parse(directionsData);
    const input = new Uint32Array(bufferValues);

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

    // Create a buffer on the GPU to hold our computation input
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

abs_code_filepath = process.argv[2]
directions_path = process.argv[3]
main(abs_code_filepath, directions_path).catch(console.error);