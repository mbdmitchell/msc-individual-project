async function main() {

  const adapter = await navigator.gpu?.requestAdapter();
  const device = await adapter?.requestDevice();
  if (!device) {
    fail('need a browser that supports WebGPU');
    return;
  }

  const module = device.createShaderModule({
    label: 'control flow compute module',
    code: `
      @group(0) @binding(0) var<storage, read_write> input_data: array<i32>;
      @group(0) @binding(1) var<storage, read_write> output_data: array<i32>;
      
      @compute @workgroup_size(1)
      fn control_flow( @builtin(global_invocation_id) id: vec3u ) 
      {
          var cntrl_ix: i32 = -1; // always incremented before use
          var output_ix: i32 = 0;
          var cntrl_val: i32;
          
          // ------ BLOCK 1 -------
          output_data[output_ix] = 1;
          output_ix++;
          // -----------------------
          while true {
              // ------ BLOCK 2 -------
              output_data[output_ix] = 2;
              output_ix++;
              // -----------------------
              cntrl_ix++;
              cntrl_val = input_data[cntrl_ix];
              if cntrl_val != 1 {
                  break;
              }
              // ------ BLOCK 3 -------
              output_data[output_ix] = 3;
              output_ix++;
              // -----------------------
              // ------ BLOCK 4 -------
              output_data[output_ix] = 4;
              output_ix++;
              // -----------------------
          }
          // ------ BLOCK 5 -------
          output_data[output_ix] = 5;
          output_ix++;
          // -----------------------
          return;
      }
    `,
  });

  const pipeline = device.createComputePipeline({
    label: 'write_twice compute pipeline',
    layout: 'auto',
    compute: {
      module,
    },
  });

  // TODO: get input from filE
  const input = new Int32Array([0]);

  // create a buffer on the GPU to hold our computation input
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
    label: 'write_twice encoder',
  });
  const pass = encoder.beginComputePass({
    label: 'write_twice compute pass',
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
  const slicedResult = resultArray.slice(0, resultArray.indexOf(0));
  const result = new Int32Array(slicedResult);

  resultBuffer.unmap();

  console.log('input', input);
  console.log('result', result);
}

function fail(msg) {
  // eslint-disable-next-line no-alert
  alert(msg);
}

main();
