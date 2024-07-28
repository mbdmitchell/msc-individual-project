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

async function run_wasm(wasmPath, directionArray, outputPath) {

    const wasmFileExists = await fileExists(wasmPath);

    if (!wasmFileExists) {
        throw new Error(`WASM file not found: ${wasmPath}`);
    }

    // CREATE INSTANCE

    // ... create importObject

    const memory = new WebAssembly.Memory({ initial: 1 });

    await populateMemoryBufferFromFile(memory, directionArray);

    var importObject = {
        js: { memory: memory }
    };

    // ... create wasmBuffer

    const wasmBuffer = fs.readFileSync(wasmPath);

    // ... instance

    const { instance } = await WebAssembly.instantiate(wasmBuffer, importObject);

    // USE INSTANCE

    instance.exports.cf(); // execute the WASM module's control flow function
    
    const memoryArray = new Int32Array(instance.exports.outputMemory.buffer, outputPath);

    printDetails(memoryArray, outputPath);

}

async function populateMemoryBufferFromFile(memory, directionArray) {

    const bufferValues = directionArray;
    const buffer = new Uint32Array(memory.buffer);

    buffer.set(bufferValues);

}

function printDetails(memoryArray, outputPath) {
    const firstZero = Array.from(memoryArray).indexOf(0);
    const data = Array.from(memoryArray.slice(0, firstZero)).join(', ');

    try {
        // Ensure the parent directory exists
        fs.mkdirSync(path.dirname(outputPath), { recursive: true });
        // Write data to the file
        fs.writeFileSync(outputPath, data, 'utf-8');
        console.log(`Data written to ${outputPath}`);
    } catch (error) {
        console.error(`Error writing to file: ${error.message}`);
    }
}

const codePath = process.argv[2];
const directionsPath = process.argv[3];
const outputPath = process.argv[4];

try {
    const directionsString = fs.readFileSync(directionsPath, 'utf-8');
    const directionArray = JSON.parse(directionsString);

    if (!Array.isArray(directionArray)) {
        throw new Error('The provided list string is not a valid array.');
    }

    run_wasm(codePath, directionArray, outputPath).catch(console.error);
} catch (error) {
    console.error('Error parsing the list string:', error.message);
    process.exit(1);
}

