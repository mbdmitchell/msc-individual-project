// e.g. % node run_manual_cf.js example.wasm

const fs = require('fs');
const path = require('path');
const util = require('util');

const readFile = util.promisify(fs.readFile);

async function fileExists(path) {
    try {
        await fs.promises.access(path);
        return true;
    } catch (error) {
        return false;
    }
}

async function run_wasm(wasmPath, directionPath) {

    const wasmFileExists = await fileExists(wasmPath);
    const directionFileExists = await fileExists(directionPath);

    if (!wasmFileExists) {
        throw new Error(`WASM file not found: ${wasmPath}`);
    }

    if (!directionFileExists) {
        throw new Error(`Direction file not found: ${directionPath}`);
    }

    // CREATE INSTANCE

    // ... create importObject

    const memory = new WebAssembly.Memory({ initial: 1 });

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

    const directionsData = await fs.promises.readFile(filePath, 'utf8');
    const bufferValues = JSON.parse(directionsData);
    const buffer = new Uint32Array(memory.buffer);

    buffer.set(bufferValues);

}

async function printDetails(memoryArray) {
    const firstZero = Array.from(memoryArray).indexOf(0);
    const data = Array.from(memoryArray.slice(0, firstZero)).join(', ');
    console.log(data)
}

const filePath = process.argv[2];
const directionPath = process.argv[3];
run_wasm(filePath, directionPath).catch(console.error);