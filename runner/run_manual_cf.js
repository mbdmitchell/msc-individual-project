// e.g. % node run_manual_cf.js example.wasm

const fs = require('fs');
const path = require('path');

async function run_manual_cf(wasmPath) {

    // CREATE INSTANCE

    // ... create importObject

    const memory = new WebAssembly.Memory({ initial: 1 });
    const directionPath= path.resolve(path.dirname(wasmPath), 'directions.txt')

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

    const outputDir = path.dirname(wasmPath);

    await writeMemoryToFile(memoryArray, outputDir);

}

async function populateMemoryBufferFromFile(memory, filePath) {

    const directionsData = await fs.promises.readFile(filePath, 'utf8'); // [0,0,4,3] correct

    const bufferValues = JSON.parse(directionsData); // [0,0,4,3] correct
    const buffer = new Uint32Array(memory.buffer);

    buffer.set(bufferValues);

}

async function writeMemoryToFile(memoryArray, outputDir) {
    const firstZero = Array.from(memoryArray).indexOf(0);
    const data = Array.from(memoryArray.slice(0, firstZero)).join(', ');

    const outputFilePath = path.resolve(outputDir, 'output.txt');

    await fs.promises.writeFile(outputFilePath, data, 'utf8');
    console.log(`Memory contents written to ${outputFilePath}`);
}

const filePath = process.argv[2];
run_manual_cf(filePath).catch(console.error);