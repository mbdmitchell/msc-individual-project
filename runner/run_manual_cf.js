// e.g. % node run_manual_cf.js example.wasm
// TODO: Low priority, reimplement in Python

const fs = require('fs');
const path = require('path');

async function run_manual_cf(wasmPath) {

    // CREATE INSTANCE

    // ... create importObject

    const memory = new WebAssembly.Memory({ initial: 1 });
    const directionPath= path.resolve(path.dirname(wasmPath), 'directions.txt')

    console.log("Directions:", directionPath)

    await populateMemoryBufferFromFile(memory, directionPath);

    var importObject = {
        js: { memory: memory }
    };

    // ... create wasmBuffer

    const wasmBuffer = fs.readFileSync(wasmPath);

    // ... instance

    const { instance } = await WebAssembly.instantiate(wasmBuffer, importObject);

    // USE INSTANCE

    instance.exports.cf(); // execute the WASM module's control flow function
    
    const memoryArray = new Int32Array(instance.exports.outputMemory.buffer);

    // PRINT OUTPUT (can redirect in shell with `> ./output.txt`

    await printDetails(memoryArray);

}

async function populateMemoryBufferFromFile(memory, filePath) {

    const directionsData = await fs.promises.readFile(filePath, 'utf8'); // [0,0,4,3] correct
    const bufferValues = JSON.parse(directionsData); // [0,0,4,3] correct
    const buffer = new Uint32Array(memory.buffer);

    buffer.set(bufferValues);

}

async function printDetails(memoryArray) {
    const firstZero = Array.from(memoryArray).indexOf(0);
    const data = Array.from(memoryArray.slice(0, firstZero)).join(', ');
    console.log(data)
}

const filePath = process.argv[2];
run_manual_cf(filePath).catch(console.error);