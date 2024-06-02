// e.g. % node run_manual_cf.js example.wasm

const fs = require('fs');
const path = require('path');

async function run_manual_cf(filePath) {

    const memory = new WebAssembly.Memory({ initial: 1 });
    await populateBufferFromFile(memory);

    var importObject = {
        js: { memory: memory }
    };

    const wasmPath = path.resolve(__dirname, filePath); 
    const wasmBuffer = fs.readFileSync(wasmPath);

    const { instance } = await WebAssembly.instantiate(wasmBuffer, importObject);
    instance.exports.cf();
    
    const memoryArray = new Int32Array(instance.exports.outputMemory.buffer);

    await writeMemoryToFile(memoryArray);

}

async function populateBufferFromFile(memory) {
    const directionsPath = path.resolve(__dirname, 'directions.txt');
    const directionsData = await fs.promises.readFile(directionsPath, 'utf8');
    const bufferValues = JSON.parse(directionsData);
    const buffer = new Uint32Array(memory.buffer);
    buffer.set(bufferValues);
}

async function writeMemoryToFile(memoryArray) {
    const firstZero = Array.from(memoryArray).indexOf(0); // Find the index of the first zero
    const data = Array.from(memoryArray.slice(0, firstZero)).join(', '); // Slice up to the first zero
    await fs.promises.writeFile('output.txt', data, 'utf8');
    console.log('Memory contents written to output.txt');
}

const filePath = process.argv[2]; 
run_manual_cf(filePath).catch(console.error);